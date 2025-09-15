use crate::data_handler::{
    create_time_stamp, get_configuration, DataSession, ServerState, SessionInfo,
};
use crate::mail_handler::mailer;
use crate::tcp_handler::{save_state, send_to_clickhouse, server_status, start_tcp_server};
use crate::tui_tool::run_tui;

use clap::{Parser, Subcommand};

use env_logger::{Builder, Target};
use log::LevelFilter;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use std::env;
use std::fmt::Debug;
use std::io;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::Arc;
use std::thread;
use std::thread::sleep;
use std::time::Duration;
use uuid::Uuid;

use std::net::TcpListener;
use std::sync::Once;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command as TokioCommand;
use tokio::sync::broadcast;
use tokio::sync::Mutex;
use tokio::task;
use tui_logger;

static LOGGER_INIT: Once = Once::new();

pub fn init_logger(log_level: LevelFilter, interactive: bool) {
    LOGGER_INIT.call_once(|| {
        if interactive {
            let _ = tui_logger::init_logger(log_level);
        } else {
            let mut builder = Builder::new();
            builder
                .filter_level(log_level)
                .target(Target::Stdout)
                .format_timestamp_secs();
            let _ = builder.try_init(); // Use try_init to be safe
        }
    });
}

pub fn get_log_level(verbosity: u8) -> LevelFilter {
    match verbosity {
        0 => LevelFilter::Error,
        1 => LevelFilter::Warn,
        2 => LevelFilter::Info,
        3 => LevelFilter::Debug,
        _ => LevelFilter::Trace,
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MinimalSessionInfo {
    pub name: String,
    pub email: String,
    pub session_name: String,
    pub session_description: String,
    pub devices: Option<HashMap<String, DeviceConfig>>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceConfig {
    #[serde(flatten)]
    pub config: HashMap<String, toml::Value>,
}

#[derive(Serialize)]
struct ConfigOverride {
    session: DataSession,
    #[serde(skip_serializing_if = "Option::is_none")]
    device: Option<HashMap<String, DeviceConfig>>,
}

impl From<MinimalSessionInfo> for DataSession {
    fn from(minimal: MinimalSessionInfo) -> Self {
        DataSession {
            start_time: None,
            end_time: None,
            uuid: None,
            info: SessionInfo {
                name: minimal.name,
                email: minimal.email,
                session_name: minimal.session_name,
                session_description: minimal.session_description,
                meta: None,
            },
        }
    }
}
/// A commandline DAQ management tool
#[derive(Parser, Debug)]
#[command(name = "rex",version, about, long_about = None)]
pub struct Cli {
    /// desired log level, info displays summary of connected instruments & recent data. debug will include all data, including standard output from Python.
    #[arg(short, long, default_value_t = 2)]
    pub verbosity: u8,
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    Run(RunArgs),
    View(StandaloneArgs),
    Serve(ServeArgs),
}

/// A commandline DAQ runner
#[derive(Parser, Debug, Clone, Deserialize, Serialize)]
#[command(version, about, long_about = None)]
pub struct RunArgs {
    /// Email address to receive results
    #[arg(short, long)]
    email: Option<String>,
    /// Time delay in minutes before starting the session
    #[arg(short, long, default_value_t = 0)]
    #[serde(default = "default_delay")]
    delay: u64,
    /// Number of times to loop the session
    #[arg(short, long, default_value_t = 1)]
    #[serde(default = "default_loops")]
    loops: u8,
    /// Path to script containing the session setup / control flow
    #[arg(short, long)]
    path: PathBuf,
    /// Dry run, will not log data. Can be used for long term monitoring
    #[arg(short = 'n', long, default_value_t = false)]
    #[serde(default = "default_dry_run")]
    dry_run: bool,
    /// Target directory for output path
    #[arg(short, long, default_value_t = get_current_dir())]
    output: String,
    /// Enable interactive TUI mode
    #[arg(short, long)]
    #[serde(default = "default_interactive")]
    pub interactive: bool,
    /// Port overide, allows for overiding default port. Will export this as environment variable for devices to utilise.
    #[arg(short = 'P', long)]
    pub port: Option<String>,
    /// Optional path to config file used by DAQ script (python, matlab etc). Useful when it is critical the script goes unmodified.,
    #[arg(short, long)]
    config: Option<String>,
    // Additional metadata that will be stored as part of the run
    #[arg(long, value_name = "JSON")]
    pub meta_json: Option<String>,
}

const fn default_delay() -> u64 {
    0
}
const fn default_dry_run() -> bool {
    false
}
const fn default_loops() -> u8 {
    1
}

const fn default_interactive() -> bool {
    false
}
/// A commandline DAQ viewer
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct StandaloneArgs {
    // Port the current session is running on. If you are running this on the same device it will be 0.0.0.0:7676
    // otherwise, please use the devices IP , device_ip:7676
    #[arg(short, long)]
    address: String,
    /// desired log level, info displays summary of connected instruments & recent data. debug will include all data, including standard output from Python.
    #[arg(short, long, default_value_t = 2)]
    verbosity: u8,
}

/// A commandline DAQ server
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct ServeArgs {
    // Port the current session is running on. If you are running this on the same device it will be 0.0.0.0:7676
    // otherwise, please use the devices IP , device_ip:7676
    #[arg(short, long, default_value_t = 9000)]
    pub address: u32,
    /// desired log level, info displays summary of connected instruments & recent data. debug will include all data, including standard output from Python.
    #[arg(short, long, default_value_t = 2)]
    pub verbosity: u8,
}

// Core CLI tool used for rex
pub fn run_session(
    args: RunArgs,
    shutdown_tx: broadcast::Sender<()>,
    log_level: LevelFilter,
    uuid: Uuid,
) {
    log::info!("Session starting in {} s", args.delay * 60);

    sleep(Duration::from_secs(&args.delay * 60));
    let interpreter_path_str = match get_configuration() {
        Ok(conf) => match conf.general.interpreter {
            interpreter => interpreter,
        },
        Err(e) => {
            log::error!("failed to get configuration due to: {e}");
            return;
        }
    };

    let interpreter_path = Arc::new(interpreter_path_str);
    let script_path = Arc::new(args.path);
    let interpreter_path_loop = Arc::clone(&interpreter_path);
    let output_path = Arc::new(args.output);
    let additional_metadata = args.meta_json.unwrap_or_default();

    if !interpreter_path_loop.is_empty() {
        for _ in 0..args.loops {
            let interpreter_path_clone = Arc::clone(&interpreter_path);
            let script_path_clone = Arc::clone(&script_path);
            log::info!("Server is starting...");

            let state = Arc::new(Mutex::new(ServerState::new(
                uuid,
                additional_metadata.clone(),
            )));

            let shutdown_rx_tcp = shutdown_tx.subscribe();
            let shutdown_rx_server_satus = shutdown_tx.subscribe();
            let shutdown_rx_logger = shutdown_tx.subscribe();
            let shutdown_rx_interpreter = shutdown_tx.subscribe();
            let shutdown_tx_clone_interpreter = shutdown_tx.clone();
            let shutdown_tx_logger = shutdown_tx.clone();
            let shutdown_tx_clone_tcp = shutdown_tx.clone();

            let tcp_state = Arc::clone(&state);
            let server_state = Arc::clone(&state);
            let server_state_ch = Arc::clone(&state);

            let config_port = match get_configuration() {
                Ok(conf) => conf.general.port,
                Err(e) => {
                    log::error!("Failed to get configuration due to: {e}");
                    return;
                }
            };

            let chosen_port = args.port.clone().unwrap_or(config_port);

            let port = if is_port_available(&chosen_port) {
                chosen_port
            } else {
                log::warn!(
                    "Port {chosen_port} is already in use, checking if a fallback port has been specified"
                );

                match args.port {
                    Some(ref fallback_port) => {
                        if fallback_port != &chosen_port {
                            log::info!("Fallback port {fallback_port} found! Using it instead");
                            fallback_port.clone()
                        } else {
                            log::error!(
                                "The fallback port is the same as the chosen one and also in use, cancelling run"
                            );
                            return;
                        }
                    }
                    None => {
                        log::error!("No fallback port specified, cancelling run");
                        return;
                    }
                }
            };

            if let Some(ref config) = args.config {
                let _ = setup_overwrite(&config);
            };
            env::set_var("REX_PORT", &port);
            env::set_var("REX_STORE", env::temp_dir());
            env::set_var("REX_UUID", uuid.to_string());

            let tui_thread = if args.interactive {
                let port_tui = port.clone();
                Some(thread::spawn(move || {
                    let rt = match tokio::runtime::Runtime::new() {
                        Ok(rt) => rt,
                        Err(e) => {
                            log::error!("Error creating Tokio runtime for TUI: {e:?}");
                            return;
                        }
                    };
                    let remote = false;
                    let addr = format!("0.0.0.0:{port_tui}");
                    match rt.block_on(run_tui(&addr, remote)) {
                        Ok(_) => log::info!("TUI closed successfully"),
                        Err(e) => log::error!("TUI encountered an error: {e}"),
                    }
                }))
            } else {
                None
            };
            let tcp_server_thread = thread::spawn(move || {
                let addr = format!("0.0.0.0:{port}");

                let rt = match tokio::runtime::Runtime::new() {
                    Ok(rt) => rt,
                    Err(e) => {
                        log::error!("Error in thread: {e:?}");
                        return;
                    }
                };
                rt.block_on(start_tcp_server(
                    addr,
                    tcp_state,
                    shutdown_rx_tcp,
                    shutdown_tx_clone_tcp,
                ))
                .unwrap();
            });

            let interpreter_thread = thread::spawn(move || {
                let rt = match tokio::runtime::Runtime::new() {
                    Ok(rt) => rt,
                    Err(e) => {
                        log::error!("Error in thread: {e:?}");
                        return;
                    }
                };

                if let Err(e) = rt.block_on(start_interpreter_process_async(
                    interpreter_path_clone,
                    script_path_clone,
                    log_level,
                    shutdown_rx_interpreter,
                )) {
                    log::error!("Python process failed: {e:?}");
                }

                if let Err(e) = shutdown_tx_clone_interpreter.send(()) {
                    log::error!("Failed to send shutdown signal: {e:?}");
                }
            });

            let printer_thread = thread::spawn(move || {
                let rt = match tokio::runtime::Runtime::new() {
                    Ok(rt) => rt,
                    Err(e) => {
                        log::error!("Error in thread: {e:?}");
                        return;
                    }
                };

                rt.block_on(server_status(server_state, shutdown_rx_server_satus))
                    .unwrap();
            });
            // Data storage

            let save_state_arc = Arc::clone(&state);
            let file_name_suffix = create_time_stamp(true);

            let output_path_clone = Arc::clone(&output_path);
            let dumper = if !args.dry_run {
                Some(thread::spawn(move || {
                    let rt = match tokio::runtime::Runtime::new() {
                        Ok(rt) => rt,
                        Err(e) => {
                            log::error!("Failed to create Tokio runtime in Dumper Thread: {e:?}");
                            return None;
                        }
                    };

                    match rt.block_on(save_state(
                        save_state_arc,
                        shutdown_rx_logger,
                        shutdown_tx_logger,
                        &file_name_suffix,
                        output_path_clone.as_ref(),
                    )) {
                        Ok(filename) => {
                            log::info!("Data storage thread completed successfully.");
                            Some(filename)
                        }
                        Err(e) => {
                            log::error!("Data storage thread encountered an error: {e:?}");
                            None
                        }
                    }
                }))
            } else {
                let rt = match tokio::runtime::Runtime::new() {
                    Ok(rt) => rt,
                    Err(e) => {
                        log::error!("Failed to create Tokio runtime in Dumper Thread: {e:?}");
                        return;
                    }
                };

                {
                    let mut state_retention = rt.block_on(state.lock());
                    state_retention.retention = false;
                    log::warn!(
                        "Setting server data retention off - No data will be written to disk"
                    )
                }
                None
            };

            let tcp_server_result = tcp_server_thread.join();
            let interpreter_thread_result = interpreter_thread.join();
            let printer_result = printer_thread.join();
            let dumper_result = match dumper {
                Some(dumper_thread) => match dumper_thread.join() {
                    Ok(resulting) => resulting,
                    Err(e) => {
                        if let Some(err) = e.downcast_ref::<String>() {
                            log::error!("Data Storage thread encountered an error: {err}");
                        } else if let Some(err) = e.downcast_ref::<&str>() {
                            log::error!("Data Storage thread encountered an error: {err}");
                        } else {
                            log::error!("Data Storage thread encountered an unknown error.");
                        }
                        None
                    }
                },
                None => None,
            };

            let results = [
                ("TCP Server Thread", tcp_server_result),
                ("Interpreter Process Thread", interpreter_thread_result),
                ("Printer Thread", printer_result),
            ];

            for (name, result) in &results {
                match result {
                    Ok(_) => log::info!("{name} shutdown successfully."),
                    Err(e) => {
                        if let Some(err) = e.downcast_ref::<String>() {
                            log::error!("{name} encountered an error: {err}");
                        } else if let Some(err) = e.downcast_ref::<&str>() {
                            log::error!("{name} encountered an error: {err}");
                        } else {
                            log::error!("{name} encountered an unknown error.");
                        }
                    }
                }
            }
            let output_file = match dumper_result {
                Some(filename) => {
                    log::info!("Data Storage Thread shutdown successfully.");
                    Some(filename)
                }
                None => {
                    log::info!(
                        "Data Storage Thread was not running, so no file output has been generated - was this a dry run?"
                    );
                    None
                }
            };
            let mut clickhouse_thread = None;
            if let Ok(config) = get_configuration() {
                if let Some(clickhouse_config) = config.click_house_server {
                    if !args.dry_run {
                        let handle = thread::spawn(move || {
                            let rt = match tokio::runtime::Runtime::new() {
                                Ok(rt) => rt,
                                Err(e) => {
                                    log::error!("Error in thread: {e:?}");
                                    return;
                                }
                            };

                            // Replace .unwrap() with proper error handling
                            match rt
                                .block_on(send_to_clickhouse(server_state_ch, clickhouse_config))
                            {
                                Ok(_) => log::info!("ClickHouse logging completed successfully"),
                                Err(e) => {
                                    if e.to_string().contains("No Session data found") {
                                        log::info!("No Session data to send to ClickHouse (likely due to quick shutdown)");
                                    } else {
                                        log::error!("ClickHouse logging failed: {e:?}");
                                    }
                                }
                            }
                        });
                        clickhouse_thread = Some(handle);
                    };
                } else {
                    log::warn!("Failed to get Clickhouse config, data will not be logged to clickhouse, however it will be logged locally");
                }
            } else {
                log::error!("Failed to get configuration.");
            };
            if let Some(tcp_handle) = clickhouse_thread {
                let handle = tcp_handle.join();
                match handle {
                    Ok(_) => log::info!("Clickhouse process shutdown sucessfully"),
                    Err(e) => log::error!("Error in thread {e:?}"),
                }
            };

            if let Some(output_file) = output_file {
                log::info!("The output file directory is: {output_path}");
                mailer(args.email.as_ref(), &output_file);
            }

            if let Some(tui_result) = tui_thread {
                let result = tui_result.join();
                match result {
                    Ok(_) => log::info!("Tui hread shutdown successfully."),
                    Err(e) => {
                        if let Some(err) = e.downcast_ref::<String>() {
                            log::error!("Tui thread encountered an error: {err}");
                        } else if let Some(err) = e.downcast_ref::<&str>() {
                            log::error!("Tui thread encountered an error: {err}");
                        } else {
                            log::error!("Tui thread encountered an unknown error.");
                        }
                    }
                }
            };
        }
    } else {
        log::error!("No interpreter path found in the arguments");
    }
}

fn get_current_dir() -> String {
    env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .to_str()
        .unwrap()
        .to_string()
}

async fn start_interpreter_process_async(
    interpreter_path: Arc<String>,
    script_path: Arc<PathBuf>,
    log_level: LevelFilter,
    mut shutdown_rx: broadcast::Receiver<()>,
) -> io::Result<()> {
    let level_str = match log_level {
        LevelFilter::Error => "ERROR",
        LevelFilter::Warn => "WARNING",
        LevelFilter::Info => "INFO",
        LevelFilter::Debug => "DEBUG",
        LevelFilter::Trace => "DEBUG",
        LevelFilter::Off => "ERROR",
    };

    let script_extension = script_path
        .as_ref()
        .extension()
        .and_then(|ext| ext.to_str());
    let optional_args = match script_extension {
        Some("py") => vec!["-u"],
        _ => vec![],
    };

    let mut interpreter_process = TokioCommand::new(interpreter_path.as_ref())
        .env("RUST_LOG_LEVEL", level_str)
        .args(&optional_args)
        .arg(script_path.as_ref())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;

    let stdout = interpreter_process
        .stdout
        .take()
        .expect("Failed to capture stdout");
    let stderr = interpreter_process
        .stderr
        .take()
        .expect("Failed to capture stderr");

    let stdout_reader = BufReader::new(stdout);
    let stderr_reader = BufReader::new(stderr);

    // Spawn async tasks for reading stdout and stderr
    let stdout_task = task::spawn(async move {
        let mut lines = stdout_reader.lines();
        while let Ok(Some(line)) = lines.next_line().await {
            log::debug!(target: "Interpreter", "{line}");
        }
    });

    let stderr_task = task::spawn(async move {
        let mut in_traceback = false;
        let mut lines = stderr_reader.lines();
        // some python specific error logging (first class support)
        while let Ok(Some(line)) = lines.next_line().await {
            if line.starts_with("Traceback (most recent call last):") {
                in_traceback = true;
                log::error!("{line}");
            } else if in_traceback {
                log::error!("{line}");
                if line.trim().is_empty() {
                    in_traceback = false;
                }
            } else if line.contains("(Ctrl+C)") {
                log::warn!("{line}");
            } else {
                log::debug!("{line}");
            }
        }
    });
    tokio::select! {
        _ = shutdown_rx.recv() => {
            log::warn!("Received shutdown signal, terminating interpreter process...");
            if let Some(id) = interpreter_process.id() {
                let _ = interpreter_process.kill().await;
                log::info!("Interpreter process (PID: {id}) terminated");
            }
        }
        status = interpreter_process.wait() => {
            log::info!("Interpreter process exited with status: {status:?}");
        }
    }
    // Wait for both stdout and stderr tasks to complete
    let _ = tokio::try_join!(stdout_task, stderr_task);

    Ok(())
}

pub fn cli_standalone(args: StandaloneArgs, log_level: LevelFilter) {
    let _ = tui_logger::init_logger(log_level);

    let tui_thread = Some(thread::spawn(move || {
        let rt = match tokio::runtime::Runtime::new() {
            Ok(rt) => rt,
            Err(e) => {
                log::error!("Error creating Tokio runtime for TUI: {e:?}");
                return;
            }
        };
        let remote = true;
        match rt.block_on(run_tui(&args.address, remote)) {
            Ok(_) => log::info!("TUI closed successfully"),
            Err(e) => log::error!("TUI encountered an error: {e}"),
        }
    }));

    if let Some(tui_result) = tui_thread {
        let result = tui_result.join();
        match result {
            Ok(_) => log::info!("Tui hread shutdown successfully."),
            Err(e) => {
                if let Some(err) = e.downcast_ref::<String>() {
                    log::error!("Tui thread encountered an error: {err}");
                } else if let Some(err) = e.downcast_ref::<&str>() {
                    log::error!("Tui thread encountered an error: {err}");
                } else {
                    log::error!("Tui thread encountered an unknown error.");
                }
            }
        }
    };
}

pub fn process_args(original_args: Vec<String>) -> Vec<String> {
    //used for removing python inserted args when rex is invoked from a python script
    let cleaned_args = original_args
        .into_iter()
        .filter(|arg| !arg.contains("python"))
        .collect();
    log::warn!("cleaned args: {cleaned_args:?}");
    cleaned_args
}

fn is_port_available(port: &str) -> bool {
    TcpListener::bind(format!("0.0.0.0:{port}")).is_ok()
}

pub fn setup_overwrite(config: &str) -> Result<(), Box<dyn std::error::Error>> {
    if std::path::Path::new(config).exists() {
        env::set_var("REX_PROVIDED_CONFIG_PATH", config);
    } else {
        match serde_json::from_str::<MinimalSessionInfo>(config) {
            Ok(data) => {
                let session: DataSession = data.clone().into();
                let devices = data.devices;
                let temp_path = create_temp_config_file(&session, devices)?;
                env::set_var(
                    "REX_PROVIDED_OVERWRITE_PATH",
                    temp_path.to_string_lossy().as_ref(),
                );
            }
            Err(e) => {
                return Err(
                    format!("Config is neither a valid file path nor valid JSON: {}", e).into(),
                );
            }
        }
    };
    Ok(())
}

fn create_temp_config_file(
    session: &DataSession,
    devices: Option<HashMap<String, DeviceConfig>>,
) -> Result<PathBuf, Box<dyn std::error::Error>> {
    let temp_dir = env::temp_dir();
    let temp_filename = format!("rex_config_{}.toml", Uuid::new_v4());
    let temp_path = temp_dir.join(temp_filename);

    let config_file = ConfigOverride {
        session: session.clone(),
        device: devices,
    };

    let toml_content = toml::to_string_pretty(&config_file)?;
    std::fs::write(&temp_path, toml_content)?;
    Ok(temp_path)
}

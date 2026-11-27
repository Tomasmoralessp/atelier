//! Runs the Python backend as a child process for local (standalone) mode.
//!
//! Release builds launch the PyInstaller binary bundled in the app resources.
//! Debug builds (`npm run tauri dev`) run `backend/run.py` from the repo venv.

use std::fs::File;
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use tauri::{AppHandle, Manager, State};

#[derive(Default)]
pub struct BackendProcess(pub Mutex<Option<Child>>);

impl BackendProcess {
    pub fn stop(&self) {
        if let Some(mut child) = self.0.lock().unwrap().take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

fn free_port() -> Result<u16, String> {
    let listener = TcpListener::bind("127.0.0.1:0").map_err(|e| e.to_string())?;
    let port = listener.local_addr().map_err(|e| e.to_string())?.port();
    Ok(port)
}

fn backend_command(app: &AppHandle) -> Result<Command, String> {
    let resources = app.path().resource_dir().map_err(|e| e.to_string())?;
    let binary = resources.join("backend").join("atelier-backend");
    let weights = resources.join("models").join("RN50-openai.safetensors");

    if binary.exists() {
        let mut command = Command::new(binary);
        if weights.exists() {
            command.env("ATELIER_MODEL_PATH", weights);
            command.env("HF_HUB_OFFLINE", "1");
        }
        return Ok(command);
    }

    if cfg!(debug_assertions) {
        let backend_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../backend");
        let mut command = Command::new(backend_dir.join(".venv/bin/python"));
        command.arg(backend_dir.join("run.py")).current_dir(&backend_dir);
        let dev_weights = backend_dir.join("models/RN50-openai.safetensors");
        if dev_weights.exists() {
            command.env("ATELIER_MODEL_PATH", dev_weights);
        }
        return Ok(command);
    }

    Err(format!("Bundled backend not found at {}", binary.display()))
}

/// Default library location, e.g. ~/Library/Application Support/Atelier.
#[tauri::command]
pub fn default_data_dir(app: AppHandle) -> Result<String, String> {
    let dir = app.path().data_dir().map_err(|e| e.to_string())?.join("Atelier");
    Ok(dir.to_string_lossy().into_owned())
}

/// (Re)start the local backend on a free port and return its base URL.
/// With `server_url` it classifies imports and stores them on that server.
#[tauri::command]
pub fn start_backend(
    app: AppHandle,
    state: State<'_, BackendProcess>,
    data_dir: String,
    server_url: Option<String>,
) -> Result<String, String> {
    state.stop();

    let port = free_port()?;
    let log_dir = app.path().app_log_dir().map_err(|e| e.to_string())?;
    std::fs::create_dir_all(&log_dir).map_err(|e| e.to_string())?;
    let log = File::create(log_dir.join("backend.log")).map_err(|e| e.to_string())?;
    let log_err = log.try_clone().map_err(|e| e.to_string())?;

    let mut command = backend_command(&app)?;
    command.args(["--data-dir", &data_dir, "--port", &port.to_string()]);
    if let Some(url) = server_url.filter(|url| !url.is_empty()) {
        command.args(["--server-url", &url]);
    }
    let child = command
        .env("ATELIER_MODE", "local")
        .stdin(Stdio::null())
        .stdout(Stdio::from(log))
        .stderr(Stdio::from(log_err))
        .spawn()
        .map_err(|e| format!("Could not start backend: {e}"))?;

    *state.0.lock().unwrap() = Some(child);
    Ok(format!("http://127.0.0.1:{port}"))
}

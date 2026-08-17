use std::env;
use std::path::PathBuf;
use std::process::Command;

fn get_python_executable() -> PathBuf {
    if let Ok(p) = env::var("PYO3_PYTHON") {
        return PathBuf::from(p);
    }
    match pyo3_build_config::get().executable() {
        Some(path) => PathBuf::from(path),
        None => {
            env::var("PYTHON_SYS_EXECUTABLE")
                .map(PathBuf::from)
                .unwrap_or_else(|_| PathBuf::from("python3"))
        }
    }
}

fn main() {
    println!("cargo::rerun-if-changed=tools/codegen.py");
    println!("cargo::rerun-if-changed=generator");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/__init__.py");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/layer.py");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/abcs/");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/functions/");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/types/");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/mtproto/layer.py");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/mtproto/abcs/");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/mtproto/functions/");
    println!("cargo::rerun-if-changed=client/src/telethon/_impl/tl/mtproto/types/");

    let manifest_dir = env::var("CARGO_MANIFEST_DIR").expect("Failed to get CARGO_MANIFEST_DIR");
    let project_root = PathBuf::from(manifest_dir);

    let generator_path = project_root.join("generator");
    let codegen_script_path = project_root.join("tools/codegen.py");

    let python_executable_path = get_python_executable();

    println!("cargo::warning=Using Python: {:?}", python_executable_path);

    let status = Command::new(&python_executable_path)
        .arg("-m")
        .arg("pip")
        .arg("install")
        .arg("--force-reinstall")
        .arg(&generator_path)
        .status()
        .expect("Failed to execute pip install generator");

    if !status.success() {
        panic!("install telethon_generator failed with status {:?}", status);
    }

    let generator_package_path = generator_path.join("src");
    let pythonpath = format!(
        "{}:{}",
        generator_package_path.to_str().unwrap(),
        env::var("PYTHONPATH").unwrap_or_default()
    );

    let status = Command::new(&python_executable_path)
        .env("PYTHONPATH", pythonpath)
        .arg(codegen_script_path)
        .status()
        .expect("Failed to execute tools/codegen.py");

    if !status.success() {
        panic!("codegen.py failed with status {:?}", status);
    }
}

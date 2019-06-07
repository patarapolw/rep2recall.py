import { app, BrowserWindow, Menu, MenuItemConstructorOptions, shell } from "electron";
import path from "path";
import { spawn } from "child_process";
import { ipcMain } from "electron";

let serverProcess = spawnServer();

let mainWindow: Electron.BrowserWindow | null;

function createWindow() {
    mainWindow = new BrowserWindow({
        height: 768,
        width: 1024,
        webPreferences: {
            nodeIntegration: true
        }
    });
    mainWindow.maximize();

    mainWindow.loadFile(path.join(__dirname, "index.html"));
    // mainWindow.webContents.openDevTools();

    const openExternalLinksInOSBrowser = (event: any, url: string) => {
        if (url.indexOf("localhost") === -1) {
            event.preventDefault();
            shell.openExternal(url);
        }
    };

    mainWindow.webContents.on("new-window", openExternalLinksInOSBrowser);
    mainWindow.webContents.on("will-navigate", openExternalLinksInOSBrowser);

    mainWindow.on("closed", () => {
        mainWindow = null;
    });
}

app.on("ready", () => {
    createWindow();

    const template: MenuItemConstructorOptions[] = [
        {
            label: "Application",
            submenu: [
                { label: "About Application", role: "about" },
                { type: "separator" },
                { label: "Quit", accelerator: "Command+Q", role: "quit" }
            ]
        },
        {
            label: "Edit",
            submenu: [
                { label: "Undo", accelerator: "CmdOrCtrl+Z", role: "undo" },
                { label: "Redo", accelerator: "Shift+CmdOrCtrl+Z", role: "redo" },
                { type: "separator" },
                { label: "Cut", accelerator: "CmdOrCtrl+X", role: "cut" },
                { label: "Copy", accelerator: "CmdOrCtrl+C", role: "copy" },
                { label: "Paste", accelerator: "CmdOrCtrl+V", role: "paste" },
                // { label: "Select All", accelerator: "CmdOrCtrl+A", role: "selectAll" }
            ]
        },
        {
            label: "Settings",
            submenu: [
                { label: "Preferences", click() {
                    mainWindow!.webContents.send("on-menu-pref");
                } }
            ]
        }
    ];

    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
});

app.on("window-all-closed", () => {
    // if (process.platform !== 'darwin') {
    serverProcess.kill();
    app.quit();
    // }
});

ipcMain.on("restart-server", () => {
    serverProcess.kill();
    serverProcess = spawnServer();
});

function spawnServer() {
    const s = spawn(path.join(
        process.versions["electron"] ? __dirname.replace("app.asar", "app.asar.unpacked") : __dirname,
        "./pyserver")
    );
    s.stdout.pipe(process.stdout);

    return s;
}

const { app, BrowserWindow, Menu, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const waitOn = require("wait-on");
const isAsar = require("electron-is-running-in-asar");
const getPort = require("get-port");
const dotenv = require("dotenv");

dotenv.config();

let serverProcess;
let mainWindow;
let PORT = {
    server: process.env.PORT || 24000
};

process.env.ROOT_PATH = path.resolve(isAsar() ? __dirname.replace("app.asar", "app.asar.unpacked") : __dirname, "..");

function createWindow() {
    mainWindow = new BrowserWindow({
        height: 768,
        width: 1024,
        webPreferences: {
            nodeIntegration: true
        }
    });
    mainWindow.maximize();

    mainWindow.loadFile(path.join(__dirname, "loading.html"));
    waitOn({resources: [`http://localhost:${PORT.server}`]}).then(() => {
        mainWindow.loadURL(`http://localhost:${PORT.server}`);
    });
    // mainWindow.webContents.openDevTools();

    const openExternalLinksInOSBrowser = (event, url) => {
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

    const template = [
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
                { label: "Select All", accelerator: "CmdOrCtrl+A", role: "selectAll" }
            ]
        },
        {
            label: "Settings",
            submenu: [
                { label: "Preferences", click() {
                    mainWindow.webContents.send("on-menu-pref");
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

(async () => {
    PORT = {
        server: process.env.PORT || await getPort({port: 24000})
    }

    process.env.PORT = PORT.server;

    serverProcess = spawn(
        path.join(
            process.env.ROOT_PATH,
            "dist/pyserver"),
        {env: process.env}
    );

    serverProcess.stdout.pipe(process.stdout);
    serverProcess.stderr.pipe(process.stderr);
})();
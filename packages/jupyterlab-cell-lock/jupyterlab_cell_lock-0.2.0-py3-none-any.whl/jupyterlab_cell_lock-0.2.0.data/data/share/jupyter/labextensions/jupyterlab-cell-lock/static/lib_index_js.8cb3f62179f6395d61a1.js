"use strict";
(self["webpackChunkjupyterlab_cell_lock"] = self["webpackChunkjupyterlab_cell_lock"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/notebook */ "webpack/sharing/consume/default/@jupyterlab/notebook");
/* harmony import */ var _jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_statusbar__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/statusbar */ "webpack/sharing/consume/default/@jupyterlab/statusbar");
/* harmony import */ var _jupyterlab_statusbar__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_statusbar__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _status__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./status */ "./lib/status.js");
/* harmony import */ var _lockIcon__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./lockIcon */ "./lib/lockIcon.js");
/* harmony import */ var _metadata__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./metadata */ "./lib/metadata.js");







const plugin = {
    id: 'jupyterlab-cell-lock:plugin',
    autoStart: true,
    requires: [_jupyterlab_notebook__WEBPACK_IMPORTED_MODULE_0__.INotebookTracker],
    optional: [_jupyterlab_statusbar__WEBPACK_IMPORTED_MODULE_1__.IStatusBar],
    activate: (app, tracker, statusBar) => {
        console.log('jupyterlab-cell-lock extension activated!');
        let statusWidget = null;
        if (statusBar) {
            statusWidget = new _status__WEBPACK_IMPORTED_MODULE_4__.CellLockStatus();
            statusBar.registerStatusItem('cellLockStatus', {
                item: statusWidget,
                align: 'middle'
            });
        }
        // Define the lock command
        const lockCommand = 'jupyterlab-cell-lock:lock-cells';
        app.commands.addCommand(lockCommand, {
            label: 'Make All Current Cells Read-Only & Undeletable',
            execute: () => {
                (0,_metadata__WEBPACK_IMPORTED_MODULE_6__.toggleCellMetadata)(false, false, tracker, statusWidget);
            }
        });
        // Define the unlock command
        const unlockCommand = 'jupyterlab-cell-lock:unlock-cells';
        app.commands.addCommand(unlockCommand, {
            label: 'Make All Current Cells Editable & Deletable',
            execute: () => {
                (0,_metadata__WEBPACK_IMPORTED_MODULE_6__.toggleCellMetadata)(true, true, tracker, statusWidget);
            }
        });
        tracker.widgetAdded.connect((_, notebookPanel) => {
            var _a;
            const { content: notebook, context } = notebookPanel;
            const lockButton = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__.ToolbarButton({
                label: 'Lock all cells',
                icon: _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.lockIcon,
                onClick: () => {
                    app.commands.execute(lockCommand);
                },
                tooltip: 'Make all current cells read-only & undeletable'
            });
            const unlockButton = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_2__.ToolbarButton({
                label: 'Unlock all cells',
                icon: _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.editIcon,
                onClick: () => {
                    app.commands.execute(unlockCommand);
                },
                tooltip: 'Make all current cells editable & deletable'
            });
            notebookPanel.toolbar.insertItem(10, 'lockCells', lockButton);
            notebookPanel.toolbar.insertItem(11, 'unlockCells', unlockButton);
            // Apply icons once the notebook is fully loaded and revealed
            Promise.all([context.ready, notebookPanel.revealed]).then(() => {
                console.log('Notebook ready and revealed, refreshing icons');
                (0,_lockIcon__WEBPACK_IMPORTED_MODULE_5__.refreshLockIcons)(notebookPanel);
            });
            // Apply icons for new cells
            (_a = notebook.model) === null || _a === void 0 ? void 0 : _a.cells.changed.connect((_, change) => {
                if (change.type === 'add') {
                    change.newValues.forEach((cellModel, idx) => {
                        const cellWidget = notebook.widgets[change.newIndex + idx];
                        if (cellWidget) {
                            // Delay slightly to ensure the cell DOM is rendered
                            setTimeout(() => {
                                (0,_lockIcon__WEBPACK_IMPORTED_MODULE_5__.applyCellLockIcon)(cellModel, cellWidget);
                            }, 20);
                        }
                    });
                }
            });
            // Refresh on metadata change
            notebook.widgets.forEach(cellWidget => {
                cellWidget.model.metadataChanged.connect(() => {
                    (0,_lockIcon__WEBPACK_IMPORTED_MODULE_5__.applyCellLockIcon)(cellWidget.model, cellWidget);
                });
            });
            // Refresh on save
            context.saveState.connect((_, state) => {
                if (state === 'completed') {
                    console.log('Notebook saved, refreshing icons...');
                    (0,_lockIcon__WEBPACK_IMPORTED_MODULE_5__.refreshLockIcons)(notebookPanel);
                }
            });
        });
        // Refresh when the active cell changes
        tracker.activeCellChanged.connect(() => {
            const current = tracker.currentWidget;
            if (current) {
                (0,_lockIcon__WEBPACK_IMPORTED_MODULE_5__.refreshLockIcons)(current);
            }
        });
    }
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ }),

/***/ "./lib/lockIcon.js":
/*!*************************!*\
  !*** ./lib/lockIcon.js ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   applyCellLockIcon: () => (/* binding */ applyCellLockIcon),
/* harmony export */   asBool: () => (/* binding */ asBool),
/* harmony export */   refreshLockIcons: () => (/* binding */ refreshLockIcons)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);

const asBool = (v) => (typeof v === 'boolean' ? v : true);
const applyCellLockIcon = (cellModel, cellWidget, retryCount = 0) => {
    const editable = asBool(cellModel.getMetadata('editable'));
    const deletable = asBool(cellModel.getMetadata('deletable'));
    const promptNode = cellWidget.node.querySelector('.jp-InputPrompt.jp-InputArea-prompt');
    if (!promptNode) {
        if (retryCount < 10) {
            setTimeout(() => {
                applyCellLockIcon(cellModel, cellWidget, retryCount + 1);
            }, 10);
        }
        return;
    }
    const existing = promptNode.querySelector('.jp-CellLockIcon');
    if (existing) {
        existing.remove();
    }
    if (!editable || !deletable) {
        const iconNode = document.createElement('span');
        iconNode.className = 'jp-CellLockIcon';
        let tooltipMessage = 'This cell is ';
        const isReadOnly = !editable;
        const isUndeletable = !deletable;
        if (isReadOnly && isUndeletable) {
            tooltipMessage += 'read-only and undeletable.';
        }
        else if (isReadOnly) {
            tooltipMessage += 'read-only but can be deleted.';
        }
        else if (isUndeletable) {
            tooltipMessage += 'undeletable but can be edited.';
        }
        iconNode.title = tooltipMessage;
        _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.lockIcon.element({
            container: iconNode,
            elementPosition: 'left',
            height: '14px',
            width: '14px'
        });
        promptNode.appendChild(iconNode);
    }
};
const refreshLockIcons = (notebookPanel) => {
    if (!notebookPanel) {
        return;
    }
    const { content: notebook } = notebookPanel;
    if (notebook.model && notebook.widgets) {
        console.log('Refreshing lock icons for', notebook.widgets.length, 'cells');
        requestAnimationFrame(() => {
            notebook.widgets.forEach((cellWidget, i) => {
                const cellModel = notebook.model.cells.get(i);
                if (cellModel) {
                    applyCellLockIcon(cellModel, cellWidget);
                }
            });
        });
    }
};


/***/ }),

/***/ "./lib/metadata.js":
/*!*************************!*\
  !*** ./lib/metadata.js ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   toggleCellMetadata: () => (/* binding */ toggleCellMetadata)
/* harmony export */ });
/* harmony import */ var _lockIcon__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./lockIcon */ "./lib/lockIcon.js");

const toggleCellMetadata = (editable, deletable, tracker, statusWidget) => {
    var _a;
    const current = tracker.currentWidget;
    if (!current) {
        console.warn('No active notebook.');
        return;
    }
    const notebook = current.content;
    const cells = (_a = notebook.model) === null || _a === void 0 ? void 0 : _a.cells;
    if (!cells) {
        return;
    }
    let editedCellCount = 0;
    let nonEditedCellCount = 0;
    for (let i = 0; i < cells.length; i++) {
        const cellModel = cells.get(i);
        const isEditable = (0,_lockIcon__WEBPACK_IMPORTED_MODULE_0__.asBool)(cellModel.getMetadata('editable'));
        const isDeletable = (0,_lockIcon__WEBPACK_IMPORTED_MODULE_0__.asBool)(cellModel.getMetadata('deletable'));
        if (isEditable !== editable || isDeletable !== deletable) {
            cellModel.setMetadata('editable', editable);
            cellModel.setMetadata('deletable', deletable);
            const cellWidget = notebook.widgets[i];
            (0,_lockIcon__WEBPACK_IMPORTED_MODULE_0__.applyCellLockIcon)(cellModel, cellWidget);
            editedCellCount++;
        }
        else {
            nonEditedCellCount++;
        }
    }
    const action = editable ? 'unlocked' : 'locked';
    let statusMessage = '';
    if (editedCellCount === 0) {
        statusMessage = `All cells were already ${action}.`;
    }
    else {
        statusMessage = `${editedCellCount} cell${editedCellCount > 1 ? 's' : ''} ${editedCellCount > 1 ? 'were' : 'was'} successfully ${action}.`;
        if (nonEditedCellCount > 0) {
            statusMessage += ` (${nonEditedCellCount} already ${action}).`;
        }
    }
    if (statusWidget) {
        statusWidget.setTemporaryStatus(statusMessage);
    }
    else {
        console.log('[CellLockStatus]', statusMessage);
    }
};


/***/ }),

/***/ "./lib/status.js":
/*!***********************!*\
  !*** ./lib/status.js ***!
  \***********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   CellLockStatus: () => (/* binding */ CellLockStatus)
/* harmony export */ });
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @lumino/widgets */ "webpack/sharing/consume/default/@lumino/widgets");
/* harmony import */ var _lumino_widgets__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_lumino_widgets__WEBPACK_IMPORTED_MODULE_0__);

class CellLockStatus extends _lumino_widgets__WEBPACK_IMPORTED_MODULE_0__.Widget {
    constructor() {
        super();
        this._timer = null;
        this.addClass('jp-CellLockStatus');
        this._statusNode = document.createElement('span');
        this.node.appendChild(this._statusNode);
        this.node.style.display = 'inline-flex';
        this.node.style.alignItems = 'center';
    }
    setTemporaryStatus(summary, timeoutMs = 4000) {
        this._statusNode.innerText = summary;
        if (this._timer) {
            window.clearTimeout(this._timer);
        }
        this._timer = window.setTimeout(() => {
            this._statusNode.innerText = '';
            this._timer = null;
        }, timeoutMs);
    }
}


/***/ })

}]);
//# sourceMappingURL=lib_index_js.8cb3f62179f6395d61a1.js.map
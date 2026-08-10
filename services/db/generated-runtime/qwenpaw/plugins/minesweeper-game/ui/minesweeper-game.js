/**
 * 扫雷游戏 - 纯逻辑类（可复用版）
 * 与 ui/index.js 的游戏规则一致，提供无 UI 依赖的核心玩法：
 *   - 棋盘生成（首点安全）
 *   - 翻开 / BFS 空白展开
 *   - 插旗 / 问号
 *   - 胜负判定
 * 使用示例：
 *   var game = new MinesweeperGame();
 *   game.init(9, 9, 10);
 *   game.reveal(3, 4);
 *   game.toggleFlag(1, 1);
 */

(function (global) {
  'use strict';

  var DIRECTIONS = [
    [-1, -1], [-1, 0], [-1, 1],
    [0, -1], [0, 1],
    [1, -1], [1, 0], [1, 1]
  ];

  function MinesweeperGame() {
    this.rows = 9;
    this.cols = 9;
    this.mines = 10;
    this.board = null;
    this.revealedCount = 0;
    this.flagsCount = 0;
    this.status = 'ready';   // ready | playing | won | lost
    this.firstClick = true;
    this.timer = 0;
  }

  MinesweeperGame.DIFFICULTIES = {
    easy:   { label: '简单', rows: 9,  cols: 9,  mines: 10 },
    medium: { label: '中等', rows: 16, cols: 16, mines: 40 },
    hard:   { label: '困难', rows: 16, cols: 30, mines: 99 }
  };

  MinesweeperGame.prototype.init = function (rows, cols, mines) {
    this.rows = rows;
    this.cols = cols;
    this.mines = mines;
    this.board = this._createBoard(rows, cols, mines, -1, -1);
    this.revealedCount = 0;
    this.flagsCount = 0;
    this.status = 'ready';
    this.firstClick = true;
    this.timer = 0;
    return this;
  };

  MinesweeperGame.prototype.initDifficulty = function (key) {
    var d = MinesweeperGame.DIFFICULTIES[key] || MinesweeperGame.DIFFICULTIES.easy;
    return this.init(d.rows, d.cols, d.mines);
  };

  MinesweeperGame.prototype._createBoard = function (rows, cols, mines, safeRow, safeCol) {
    var board = [];
    for (var r = 0; r < rows; r++) {
      board.push([]);
      for (var c = 0; c < cols; c++) {
        board[r].push({ mine: false, revealed: false, flag: false, question: false, adjacent: 0, justHit: false });
      }
    }
    var placed = 0;
    var tries = 0;
    var maxTries = rows * cols * 20;
    while (placed < mines && tries < maxTries) {
      var mr = Math.floor(Math.random() * rows);
      var mc = Math.floor(Math.random() * cols);
      if (safeRow >= 0 && Math.abs(mr - safeRow) <= 1 && Math.abs(mc - safeCol) <= 1) {
        tries++;
        continue;
      }
      if (!board[mr][mc].mine) {
        board[mr][mc].mine = true;
        placed++;
      }
      tries++;
    }
    for (var r2 = 0; r2 < rows; r2++) {
      for (var c2 = 0; c2 < cols; c2++) {
        if (!board[r2][c2].mine) {
          board[r2][c2].adjacent = this._countAdjacent(board, r2, c2);
        }
      }
    }
    return board;
  };

  MinesweeperGame.prototype._countAdjacent = function (board, r, c) {
    var count = 0;
    for (var i = 0; i < DIRECTIONS.length; i++) {
      var nr = r + DIRECTIONS[i][0];
      var nc = c + DIRECTIONS[i][1];
      if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols && board[nr][nc].mine) {
        count++;
      }
    }
    return count;
  };

  /** 翻开格子，返回 { hitMine, won } */
  MinesweeperGame.prototype.reveal = function (r, c) {
    if (this.status === 'won' || this.status === 'lost') return { hitMine: false, won: false };
    if (r < 0 || r >= this.rows || c < 0 || c >= this.cols) return { hitMine: false, won: false };

    var cell = this.board[r][c];
    if (cell.revealed || cell.flag) return { hitMine: false, won: false };

    if (this.firstClick) {
      this.firstClick = false;
      this.board = this._createBoard(this.rows, this.cols, this.mines, r, c);
      cell = this.board[r][c];
      this.status = 'playing';
    }

    if (cell.mine) {
      cell.revealed = true;
      cell.justHit = true;
      this.status = 'lost';
      this._revealAllMines();
      return { hitMine: true, won: false };
    }

    var stack = [[r, c]];
    while (stack.length) {
      var pos = stack.pop();
      var cr = pos[0], cc = pos[1];
      var cur = this.board[cr][cc];
      if (cur.revealed || cur.flag || cur.mine) continue;
      cur.revealed = true;
      this.revealedCount++;
      if (cur.adjacent === 0) {
        for (var i = 0; i < DIRECTIONS.length; i++) {
          var nr = cr + DIRECTIONS[i][0];
          var nc = cc + DIRECTIONS[i][1];
          if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols &&
              !this.board[nr][nc].revealed && !this.board[nr][nc].flag) {
            stack.push([nr, nc]);
          }
        }
      }
    }

    if (this.revealedCount === this.rows * this.cols - this.mines) {
      this.status = 'won';
      this._flagAllMines();
      return { hitMine: false, won: true };
    }
    return { hitMine: false, won: false };
  };

  /** 右键循环：空 -> 旗 -> 问号 -> 空 */
  MinesweeperGame.prototype.toggleFlag = function (r, c) {
    if (this.status === 'won' || this.status === 'lost') return;
    if (r < 0 || r >= this.rows || c < 0 || c >= this.cols) return;
    var cell = this.board[r][c];
    if (cell.revealed) return;
    if (!cell.flag && !cell.question) {
      cell.flag = true;
      this.flagsCount++;
    } else if (cell.flag) {
      cell.flag = false;
      cell.question = true;
      this.flagsCount--;
    } else {
      cell.question = false;
    }
  };

  MinesweeperGame.prototype._revealAllMines = function () {
    for (var r = 0; r < this.rows; r++) {
      for (var c = 0; c < this.cols; c++) {
        if (this.board[r][c].mine) this.board[r][c].revealed = true;
      }
    }
  };

  MinesweeperGame.prototype._flagAllMines = function () {
    for (var r = 0; r < this.rows; r++) {
      for (var c = 0; c < this.cols; c++) {
        if (this.board[r][c].mine && !this.board[r][c].flag) {
          this.board[r][c].flag = true;
          this.flagsCount++;
        }
      }
    }
  };

  MinesweeperGame.prototype.minesLeft = function () {
    return this.mines - this.flagsCount;
  };

  MinesweeperGame.prototype.isOver = function () {
    return this.status === 'won' || this.status === 'lost';
  };

  global.MinesweeperGame = MinesweeperGame;
})(typeof window !== 'undefined' ? window : globalThis);

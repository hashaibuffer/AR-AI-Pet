(function () {
  'use strict';

  if (!window.QwenPaw || !window.QwenPaw.host) {
    console.error("[minesweeper-game] QwenPaw not ready");
    return;
  }

  var QP = window.QwenPaw;
  var React = QP.host.React;
  var h = React.createElement;
  var e = React.createElement;

  var PLUGIN_ID = "minesweeper-game";

  // ============ 难度设置 ============
  var DIFFICULTIES = {
    easy:   { label: '简单', rows: 9,  cols: 9,  mines: 10, color: '#4CAF50', icon: '🟢' },
    medium: { label: '中等', rows: 16, cols: 16, mines: 40, color: '#FF9800', icon: '🟡' },
    hard:   { label: '困难', rows: 16, cols: 30, mines: 99, color: '#f44336', icon: '🔴' }
  };

  // 经典扫雷数字配色
  var NUM_COLORS = {
    1: '#0000ff', 2: '#008000', 3: '#ff0000',
    4: '#000080', 5: '#800000', 6: '#008080',
    7: '#000000', 8: '#808080'
  };

  // ============ 游戏状态 ============
  var state = {
    rows: 9,
    cols: 9,
    mines: 10,
    board: null,          // 每个格子: { mine, revealed, flag, question, adjacent, justHit }
    revealedCount: 0,
    flagsCount: 0,
    status: 'ready',      // ready | playing | won | lost
    firstClick: true,
    timer: 0,
    timerInterval: null,
    currentDifficulty: 'easy',
    canvas: null,
    ctx: null,
    cellSize: 34
  };

  // ============ 棋盘生成 ============
  function countAdjacentMines(board, r, c) {
    var count = 0;
    for (var dr = -1; dr <= 1; dr++) {
      for (var dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        var nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < state.rows && nc >= 0 && nc < state.cols && board[nr][nc].mine) {
          count++;
        }
      }
    }
    return count;
  }

  // safeRow/safeCol < 0 表示无安全区（用于开局预览）
  function createBoard(rows, cols, mines, safeRow, safeCol) {
    var board = [];
    for (var r = 0; r < rows; r++) {
      board.push([]);
      for (var c = 0; c < cols; c++) {
        board[r].push({ mine: false, revealed: false, flag: false, question: false, adjacent: 0, justHit: false });
      }
    }
    var placed = 0;
    var maxTries = rows * cols * 20;
    var tries = 0;
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
          board[r2][c2].adjacent = countAdjacentMines(board, r2, c2);
        }
      }
    }
    return board;
  }

  // ============ 核心玩法 ============
  function reveal(r, c) {
    if (state.status === 'won' || state.status === 'lost') return;
    if (r < 0 || r >= state.rows || c < 0 || c >= state.cols) return;

    var cell = state.board[r][c];
    if (cell.revealed || cell.flag) return;

    // 首次点击：重新生成棋盘，保证首点及其 3x3 安全
    if (state.firstClick) {
      state.firstClick = false;
      state.board = createBoard(state.rows, state.cols, state.mines, r, c);
      cell = state.board[r][c];
      startTimer();
      state.status = 'playing';
    }

    if (cell.mine) {
      cell.revealed = true;
      cell.justHit = true;
      gameOver();
      return;
    }

    // BFS 展开空白区域
    var stack = [[r, c]];
    while (stack.length) {
      var pos = stack.pop();
      var cr = pos[0], cc = pos[1];
      var cur = state.board[cr][cc];
      if (cur.revealed || cur.flag || cur.mine) continue;
      cur.revealed = true;
      state.revealedCount++;
      if (cur.adjacent === 0) {
        for (var dr = -1; dr <= 1; dr++) {
          for (var dc = -1; dc <= 1; dc++) {
            if (dr === 0 && dc === 0) continue;
            var nr = cr + dr, nc = cc + dc;
            if (nr >= 0 && nr < state.rows && nc >= 0 && nc < state.cols &&
                !state.board[nr][nc].revealed && !state.board[nr][nc].flag) {
              stack.push([nr, nc]);
            }
          }
        }
      }
    }

    if (state.revealedCount === state.rows * state.cols - state.mines) {
      winGame();
      return;
    }
    updateInfo();
    draw();
  }

  // 左键双击数字：快速翻开周围（可选辅助，当前未启用）
  function toggleFlag(r, c) {
    if (state.status === 'won' || state.status === 'lost') return;
    if (r < 0 || r >= state.rows || c < 0 || c >= state.cols) return;
    var cell = state.board[r][c];
    if (cell.revealed) return;
    if (!cell.flag && !cell.question) {
      cell.flag = true;
      state.flagsCount++;
    } else if (cell.flag) {
      cell.flag = false;
      cell.question = true;
      state.flagsCount--;
    } else {
      cell.question = false;
    }
    updateInfo();
    draw();
  }

  function gameOver() {
    state.status = 'lost';
    stopTimer();
    // 展示所有雷
    for (var r = 0; r < state.rows; r++) {
      for (var c = 0; c < state.cols; c++) {
        if (state.board[r][c].mine) state.board[r][c].revealed = true;
      }
    }
    draw();
    showOverlay('lost');
  }

  function winGame() {
    state.status = 'won';
    stopTimer();
    // 自动为所有雷插旗
    for (var r = 0; r < state.rows; r++) {
      for (var c = 0; c < state.cols; c++) {
        if (state.board[r][c].mine && !state.board[r][c].flag) {
          state.board[r][c].flag = true;
          state.flagsCount++;
        }
      }
    }
    updateInfo();
    draw();
    showOverlay('won');
  }

  // ============ 计时 ============
  function startTimer() {
    stopTimer();
    state.timerInterval = setInterval(function () {
      state.timer++;
      if (state.timer > 999) state.timer = 999;
      updateInfo();
    }, 1000);
  }

  function stopTimer() {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  }

  function formatTime(sec) {
    var s = String(sec);
    while (s.length < 3) s = '0' + s;
    return s;
  }

  // ============ 绘制 ============
  function computeCellSize() {
    var byCols = Math.floor(640 / state.cols);
    var byRows = Math.floor(480 / state.rows);
    var size = Math.min(34, byCols, byRows);
    return Math.max(16, size);
  }

  function drawUnrevealedCell(x, y, cell) {
    var ctx = state.ctx;
    ctx.fillStyle = '#bdbdbd';
    ctx.fillRect(x, y, cell, cell);
    // 左上亮边
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(x, y, cell, 2);
    ctx.fillRect(x, y, 2, cell);
    // 右下暗边
    ctx.fillStyle = '#7b7b7b';
    ctx.fillRect(x, y + cell - 2, cell, 2);
    ctx.fillRect(x + cell - 2, y, 2, cell);
    // 中间
    ctx.fillStyle = '#c6c6c6';
    ctx.fillRect(x + 2, y + 2, cell - 4, cell - 4);
  }

  function drawMine(x, y, cell, justHit) {
    var ctx = state.ctx;
    var cx = x + cell / 2;
    var cy = y + cell / 2;
    var radius = cell * 0.26;
    if (justHit) {
      ctx.fillStyle = '#e53935';
      ctx.fillRect(x, y, cell, cell);
    }
    // 尖刺
    ctx.strokeStyle = '#111111';
    ctx.lineWidth = Math.max(1, cell * 0.07);
    for (var i = 0; i < 8; i++) {
      var angle = (Math.PI / 4) * i;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
      ctx.lineTo(cx + Math.cos(angle) * (radius + cell * 0.15), cy + Math.sin(angle) * (radius + cell * 0.15));
      ctx.stroke();
    }
    // 球体
    ctx.fillStyle = '#222222';
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
    // 高光
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(cx - radius * 0.3, cy - radius * 0.35, radius * 0.25, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawFlag(x, y, cell) {
    var ctx = state.ctx;
    var cx = x + cell * 0.35;
    var top = y + cell * 0.15;
    // 旗杆
    ctx.fillStyle = '#333333';
    ctx.fillRect(cx - 1, top, 2, cell * 0.62);
    // 旗面
    ctx.fillStyle = '#e53935';
    ctx.beginPath();
    ctx.moveTo(cx + 1, top);
    ctx.lineTo(cx + cell * 0.62, y + cell * 0.3);
    ctx.lineTo(cx + 1, y + cell * 0.46);
    ctx.closePath();
    ctx.fill();
    // 底座
    ctx.fillStyle = '#333333';
    ctx.fillRect(cx - cell * 0.18, y + cell * 0.77, cell * 0.3, cell * 0.07);
  }

  function draw() {
    if (!state.ctx || !state.board) return;
    var cell = state.cellSize;
    var w = state.cols * cell;
    var h = state.rows * cell;
    state.canvas.width = w;
    state.canvas.height = h;

    state.ctx.fillStyle = '#9e9e9e';
    state.ctx.fillRect(0, 0, w, h);

    for (var r = 0; r < state.rows; r++) {
      for (var c = 0; c < state.cols; c++) {
        var cs = state.board[r][c];
        var x = c * cell, y = r * cell;
        if (cs.revealed) {
          state.ctx.fillStyle = '#d5d5d5';
          state.ctx.fillRect(x, y, cell, cell);
          state.ctx.strokeStyle = '#b0b0b0';
          state.ctx.lineWidth = 1;
          state.ctx.strokeRect(x + 0.5, y + 0.5, cell - 1, cell - 1);
          if (cs.mine) {
            drawMine(x, y, cell, cs.justHit);
          } else if (cs.adjacent > 0) {
            state.ctx.fillStyle = NUM_COLORS[cs.adjacent] || '#000000';
            state.ctx.font = 'bold ' + Math.floor(cell * 0.62) + 'px system-ui, sans-serif';
            state.ctx.textAlign = 'center';
            state.ctx.textBaseline = 'middle';
            state.ctx.fillText(String(cs.adjacent), x + cell / 2, y + cell / 2 + 1);
          }
        } else {
          drawUnrevealedCell(x, y, cell);
          if (cs.flag) {
            drawFlag(x, y, cell);
          } else if (cs.question) {
            state.ctx.fillStyle = '#000000';
            state.ctx.font = 'bold ' + Math.floor(cell * 0.6) + 'px system-ui, sans-serif';
            state.ctx.textAlign = 'center';
            state.ctx.textBaseline = 'middle';
            state.ctx.fillText('?', x + cell / 2, y + cell / 2 + 1);
          }
        }
      }
    }
  }

  // ============ UI 信息 ============
  function updateInfo() {
    var mineLeft = document.getElementById('ms-mines-left');
    var timerEl = document.getElementById('ms-timer');
    var diffEl = document.getElementById('ms-difficulty');
    if (mineLeft) mineLeft.textContent = String(Math.max(-99, state.mines - state.flagsCount));
    if (timerEl) timerEl.textContent = formatTime(state.timer);
    if (diffEl) diffEl.textContent = DIFFICULTIES[state.currentDifficulty].label;
  }

  function showOverlay(result) {
    var overlay = document.getElementById('ms-overlay');
    var title = document.getElementById('ms-overlay-title');
    var info = document.getElementById('ms-overlay-info');
    if (!overlay) return;
    if (result === 'won') {
      title.textContent = '🎉 恭喜通关！';
      info.textContent = '用时 ' + state.timer + ' 秒，成功排除全部 ' + state.mines + ' 颗雷';
    } else {
      title.textContent = '💥 踩到地雷了';
      info.textContent = '坚持了 ' + state.timer + ' 秒，再接再厉！';
    }
    overlay.style.display = 'flex';
  }

  // ============ 本地参谋智能体 ============
  function serializeBoard() {
    if (!state.board) return '';
    var lines = [];
    for (var r = 0; r < state.rows; r++) {
      var cells = [];
      for (var c = 0; c < state.cols; c++) {
        var cs = state.board[r][c];
        if (cs.revealed) {
          if (cs.mine) cells.push('X');
          else if (cs.adjacent > 0) cells.push(String(cs.adjacent));
          else cells.push('.');
        } else if (cs.flag) {
          cells.push('F');
        } else if (cs.question) {
          cells.push('Q');
        } else {
          cells.push('?');
        }
      }
      lines.push('行' + r + ': ' + cells.join(' '));
    }
    return lines.join('\n');
  }

  function setAdvice(text, loading) {
    var box = document.getElementById('ms-advice-content');
    var btn = document.getElementById('ms-advice-btn');
    if (box) {
      box.textContent = text;
      box.style.color = loading ? '#8899aa' : '#d0e0f0';
    }
    if (btn) btn.disabled = !!loading;
  }

  function askSage() {
    if (!state.board) return;
    if (state.status === 'won' || state.status === 'lost') {
      setAdvice('这局已经结束啦，开新局再找我吧 😊', false);
      return;
    }
    if (state.firstClick) {
      setAdvice('先点开第一格，我才能看清局面哦 😉', false);
      return;
    }
    var payload = {
      rows: state.rows,
      cols: state.cols,
      mines: state.mines,
      revealed_count: state.revealedCount,
      flags_count: state.flagsCount,
      status: state.status,
      timer: state.timer,
      board_text: serializeBoard()
    };
    setAdvice('🤔 参谋正在分析盘面，请稍候…', true);
    fetch('/api/minesweeper-game/advice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (data && data.ok) {
          setAdvice('🤝 ' + data.advice, false);
        } else {
          setAdvice('⚠️ ' + ((data && data.error) || '参谋暂时无法回答'), false);
        }
      })
      .catch(function (err) {
        setAdvice('⚠️ 请求失败：' + err.message, false);
      });
  }

  // ============ 事件 ============
  function handleCanvasMouseDown(ev) {
    ev.preventDefault();
    var rect = state.canvas.getBoundingClientRect();
    var x = ev.clientX - rect.left;
    var y = ev.clientY - rect.top;
    var c = Math.floor(x / state.cellSize);
    var r = Math.floor(y / state.cellSize);
    if (r < 0 || r >= state.rows || c < 0 || c >= state.cols) return;
    if (ev.button === 2) {
      toggleFlag(r, c);
    } else if (ev.button === 0) {
      reveal(r, c);
    }
  }

  function bindCanvasEvents() {
    if (!state.canvas) return;
    state.canvas.onmousedown = handleCanvasMouseDown;
    state.canvas.oncontextmenu = function (ev) {
      if (ev) ev.preventDefault();
      return false;
    };
  }

  // ============ 流程控制 ============
  function startGame(key) {
    var d = DIFFICULTIES[key];
    if (!d) return;
    stopTimer();
    state.rows = d.rows;
    state.cols = d.cols;
    state.mines = d.mines;
    state.currentDifficulty = key;
    state.board = createBoard(d.rows, d.cols, d.mines, -1, -1);
    state.revealedCount = 0;
    state.flagsCount = 0;
    state.status = 'ready';
    state.firstClick = true;
    state.timer = 0;

    var canvas = document.getElementById('ms-canvas');
    if (!canvas) {
      console.error('[minesweeper-game] Canvas not found');
      return;
    }
    state.canvas = canvas;
    state.ctx = canvas.getContext('2d');
    state.cellSize = computeCellSize();

    bindCanvasEvents();
    updateInfo();
    draw();

    var menu = document.getElementById('ms-menu-screen');
    var game = document.getElementById('ms-game-screen');
    if (menu) menu.style.display = 'none';
    if (game) game.style.display = 'flex';
    console.log('[minesweeper-game] Game started:', key, d.rows + 'x' + d.cols, d.mines + ' mines');
  }

  function restart() {
    var overlay = document.getElementById('ms-overlay');
    if (overlay) overlay.style.display = 'none';
    startGame(state.currentDifficulty);
  }

  function backToMenu() {
    stopTimer();
    var menu = document.getElementById('ms-menu-screen');
    var game = document.getElementById('ms-game-screen');
    var overlay = document.getElementById('ms-overlay');
    if (menu) menu.style.display = 'flex';
    if (game) game.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
  }

  function cleanup() {
    stopTimer();
    if (state.canvas) {
      state.canvas.onmousedown = null;
      state.canvas.oncontextmenu = null;
      state.canvas = null;
      state.ctx = null;
    }
  }

  // ============ 样式 ============
  var gameStyles = {
    container: {
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'flex-start',
      minHeight: '100vh', background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif'
    },
    title: {
      fontSize: '36px', fontWeight: 'bold', color: '#ffd166',
      marginBottom: '16px', textShadow: '0 0 20px rgba(255,209,102,0.5)'
    },
    subtitle: { color: '#8899aa', marginBottom: '24px', fontSize: '14px' },
    menuScreen: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', padding: '40px 20px' },
    difficultyButton: { width: '220px', padding: '16px', fontSize: '17px', margin: '4px', borderRadius: '8px', border: 'none', cursor: 'pointer', color: '#fff', fontWeight: 'bold', boxShadow: '0 4px 14px rgba(0,0,0,0.35)' },
    gameWrapper: { display: 'flex', gap: '24px', alignItems: 'flex-start', flexWrap: 'wrap', justifyContent: 'center' },
    canvasContainer: { position: 'relative', border: '3px solid #ffd166', borderRadius: '8px', boxShadow: '0 0 30px rgba(255,209,102,0.3)' },
    canvas: { display: 'block', background: '#9e9e9e' },
    sidePanel: { display: 'flex', flexDirection: 'column', gap: '14px', minWidth: '180px' },
    panel: { background: 'rgba(255,255,255,0.1)', borderRadius: '8px', padding: '14px', border: '1px solid rgba(255,255,255,0.2)' },
    panelTitle: { fontSize: '13px', color: '#8899aa', marginBottom: '6px' },
    panelValue: { fontSize: '26px', fontWeight: 'bold', color: '#ffd166', fontVariantNumeric: 'tabular-nums' },
    button: { padding: '12px 20px', fontSize: '15px', fontWeight: 'bold', border: 'none', borderRadius: '6px', cursor: 'pointer' },
    controls: { marginTop: '20px', padding: '14px 18px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', color: '#8899aa', fontSize: '13px', textAlign: 'center', lineHeight: '1.7' },
    footer: { marginTop: 'auto', padding: '14px 10px', color: '#667788', fontSize: '12px', textAlign: 'center', borderTop: '1px solid rgba(255,255,255,0.08)', width: '100%' },
    overlay: {
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.88)', display: 'none',
      flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      zIndex: 100, borderRadius: '6px', gap: '14px'
    },
    overlayTitle: { fontSize: '30px', fontWeight: 'bold', color: '#ffffff', marginBottom: '4px' },
    overlayInfo: { color: '#aabbcc', fontSize: '16px', marginBottom: '10px' }
  };

  // ============ React 组件 ============
  function MinesweeperComponent() {
    React.useEffect(function () {
      console.log('[minesweeper-game] Component mounted');
      return cleanup;
    }, []);

    var menuScreen = e('div', { key: 'menu', id: 'ms-menu-screen', style: gameStyles.menuScreen }, [
      e('h1', { style: gameStyles.title }, '💣 扫雷'),
      e('p', { style: gameStyles.subtitle }, '经典逻辑游戏 · 首点安全 · 不靠运气靠推理'),
      e('div', { style: { display: 'flex', flexDirection: 'column', gap: '6px' } }, [
        e('button', {
          style: Object.assign({}, gameStyles.button, gameStyles.difficultyButton, { background: 'linear-gradient(135deg, #4CAF50, #2e7d32)' }),
          onClick: function () { startGame('easy'); }
        }, '🟢 简单  9×9 · 10 雷'),
        e('button', {
          style: Object.assign({}, gameStyles.button, gameStyles.difficultyButton, { background: 'linear-gradient(135deg, #FF9800, #e65100)' }),
          onClick: function () { startGame('medium'); }
        }, '🟡 中等  16×16 · 40 雷'),
        e('button', {
          style: Object.assign({}, gameStyles.button, gameStyles.difficultyButton, { background: 'linear-gradient(135deg, #f44336, #b71c1c)' }),
          onClick: function () { startGame('hard'); }
        }, '🔴 困难  30×16 · 99 雷')
      ]),
      e('div', { style: gameStyles.controls }, [
        e('p', null, '玩法说明：'),
        e('p', null, '左键 翻开格子 | 右键 插旗/问号 | 数字 = 周围雷数'),
        e('p', null, '翻开数字 0 会自动展开相邻空白区域')
      ]),
      e('div', { style: { marginTop: '26px', padding: '12px 26px', background: 'rgba(255,209,102,0.12)', border: '1px solid rgba(255,209,102,0.4)', borderRadius: '8px', color: '#ffd166', fontSize: '13px', fontWeight: 'bold', textAlign: 'center' } }, 'Powered by CloudPaw · 灵感来自 Mineswifter'),
      e('div', { key: 'invite', style: { marginTop: '18px', padding: '12px 26px', background: 'rgba(124,77,255,0.15)', border: '1px solid rgba(124,77,255,0.45)', borderRadius: '8px', color: '#dcd0ff', fontSize: '12px', lineHeight: '1.8', textAlign: 'center', maxWidth: '440px' } }, [
        e('span', null, 'Cshu邀请您进入AI群，了解扫雷应用开发全流程，链接如下：'),
        e('br', null),
        e('a', { href: 'https://nightly.paw.msgbyte.com/invite/hU_bX9jh', target: '_blank', rel: 'noopener noreferrer', style: { color: '#ffd166', fontWeight: 'bold', wordBreak: 'break-all' } }, 'https://nightly.paw.msgbyte.com/invite/hU_bX9jh')
      ])
    ]);

    var gameScreen = e('div', { key: 'game', id: 'ms-game-screen', style: Object.assign({}, gameStyles.container, { display: 'none' }) }, [
      e('h1', { style: gameStyles.title }, '💣 扫雷'),
      e('div', { style: gameStyles.gameWrapper }, [
        e('div', { style: gameStyles.canvasContainer }, [
          e('canvas', { id: 'ms-canvas', style: gameStyles.canvas }),
          e('div', { id: 'ms-overlay', style: gameStyles.overlay }, [
            e('div', { id: 'ms-overlay-title', style: gameStyles.overlayTitle }, ''),
            e('p', { id: 'ms-overlay-info', style: gameStyles.overlayInfo }, ''),
            e('div', { style: { display: 'flex', gap: '12px' } }, [
              e('button', { style: Object.assign({}, gameStyles.button, { background: 'linear-gradient(135deg, #ffd166, #f5b800)', color: '#1a1a2e' }), onClick: restart }, '🔄 再来一局'),
              e('button', { style: Object.assign({}, gameStyles.button, { background: 'rgba(255,255,255,0.12)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }), onClick: backToMenu }, '返回菜单')
            ])
          ])
        ]),
        e('div', { style: gameStyles.sidePanel }, [
          e('div', { style: gameStyles.panel }, [
            e('div', { style: gameStyles.panelTitle }, '💣 剩余雷数'),
            e('div', { id: 'ms-mines-left', style: gameStyles.panelValue }, '10')
          ]),
          e('div', { style: gameStyles.panel }, [
            e('div', { style: gameStyles.panelTitle }, '⏱ 用时'),
            e('div', { id: 'ms-timer', style: gameStyles.panelValue }, '000')
          ]),
          e('div', { style: gameStyles.panel }, [
            e('div', { style: gameStyles.panelTitle }, '🎯 难度'),
            e('div', { id: 'ms-difficulty', style: gameStyles.panelValue }, '简单')
          ]),
          e('div', { style: { display: 'flex', flexDirection: 'column', gap: '10px' } }, [
            e('button', { id: 'ms-advice-btn', style: Object.assign({}, gameStyles.button, { background: 'linear-gradient(135deg, #7c4dff, #4a148c)', color: '#fff' }), onClick: askSage }, '🤝 请参谋出招'),
            e('button', { style: Object.assign({}, gameStyles.button, { background: 'rgba(255,209,102,0.25)', color: '#ffd166', border: '1px solid rgba(255,209,102,0.5)' }), onClick: restart }, '🔄 重新开始'),
            e('button', { style: Object.assign({}, gameStyles.button, { background: 'rgba(255,255,255,0.1)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }), onClick: backToMenu }, '🏠 返回菜单')
          ]),
          e('div', { style: Object.assign({}, gameStyles.panel, { maxWidth: '260px' }) }, [
            e('div', { style: gameStyles.panelTitle }, '🧠 参谋建议'),
            e('div', { id: 'ms-advice-content', style: { color: '#8899aa', fontSize: '13px', lineHeight: '1.7', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '220px', overflowY: 'auto' } }, '点击「🤝 请参谋出招」，本地扫雷参谋会分析盘面并给出建议')
          ])
        ])
      ]),
      e('div', { style: gameStyles.controls }, [
        e('p', null, '左键 翻开 | 右键 插旗/问号 | 翻完所有安全格即获胜')
      ]),
      e('div', { key: 'invite', style: { marginTop: '16px', padding: '10px 26px', background: 'rgba(124,77,255,0.15)', border: '1px solid rgba(124,77,255,0.45)', borderRadius: '8px', color: '#dcd0ff', fontSize: '12px', lineHeight: '1.8', textAlign: 'center', maxWidth: '560px' } }, [
        e('span', null, 'Cshu邀请您进入AI群，了解扫雷应用开发全流程，链接如下：'),
        e('br', null),
        e('a', { href: 'https://nightly.paw.msgbyte.com/invite/hU_bX9jh', target: '_blank', rel: 'noopener noreferrer', style: { color: '#ffd166', fontWeight: 'bold', wordBreak: 'break-all' } }, 'https://nightly.paw.msgbyte.com/invite/hU_bX9jh')
      ])
    ]);

    return e('div', { style: Object.assign({}, gameStyles.container, { justifyContent: 'flex-start' }) }, [
      menuScreen,
      gameScreen,
      e('div', { key: 'footer', style: gameStyles.footer }, '作者：0+1+2≠3 Team 115886')
    ]);
  }

  // ============ 注册 ============
  if (QP.registerRoutes) {
    try {
      QP.registerRoutes(PLUGIN_ID, [{ path: "/apps/minesweeper-game", component: MinesweeperComponent, label: "扫雷", icon: "💣" }]);
      console.info("[" + PLUGIN_ID + "] registered via registerRoutes");
    } catch (err) {
      console.warn("[" + PLUGIN_ID + "] registerRoutes failed:", err);
    }
  }

  if (QP.menu && QP.menu.add) {
    try {
      QP.menu.add(PLUGIN_ID, [{
        id: PLUGIN_ID + ".menu",
        location: "primary.settings",
        label: "扫雷",
        icon: function () { return h("span", { style: { fontSize: 18 } }, "💣"); },
        route: PLUGIN_ID + ".home",
        order: 80
      }]);
      console.info("[" + PLUGIN_ID + "] registered via menu.add");
    } catch (err) {
      console.warn("[" + PLUGIN_ID + "] menu.add failed:", err);
    }
  }

  if (QP.route && QP.route.add) {
    try {
      QP.route.add(PLUGIN_ID, [{ id: PLUGIN_ID + ".home", path: "/plugin/minesweeper-game", component: MinesweeperComponent }]);
      console.info("[" + PLUGIN_ID + "] registered via route.add");
    } catch (err) {
      console.warn("[" + PLUGIN_ID + "] route.add failed:", err);
    }
  }

  console.info("[minesweeper-game] Plugin loaded");
})();

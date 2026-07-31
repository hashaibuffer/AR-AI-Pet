"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type Slide = {
  kicker: string;
  title: string;
  subtitle?: string;
  kind:
    | "cover"
    | "problem"
    | "thesis"
    | "roles"
    | "solo"
    | "life"
    | "loop"
    | "social"
    | "privacy"
    | "prototype"
    | "stack"
    | "roadmap"
    | "boundary"
    | "budgets"
    | "opensource";
};

const slides: Slide[] = [
  {
    kicker: "GOAI 2026 · 无界应用 · AI + 眼镜",
    title: "AI 不只活在屏幕里",
    subtitle: "AgentOS × StackChan × XREAL One Pro",
    kind: "cover",
  },
  {
    kicker: "01 · 为什么现在",
    title: "今天的 AI 很聪明，却不在你身边",
    subtitle: "信息、陪伴与行动分散在不同屏幕，缺少一个持续存在的角色。",
    kind: "problem",
  },
  {
    kicker: "02 · 核心主张",
    title: "一个数字分身，两种存在方式",
    subtitle: "AgentOS 是电子世界中的“我”，机器人是它在现实中的陪伴化身。",
    kind: "thesis",
  },
  {
    kicker: "03 · 产品形态",
    title: "五个端，不是五套产品",
    subtitle: "统一人格与记忆，各端只做自己最擅长的事。",
    kind: "roles",
  },
  {
    kicker: "04 · 一人一机",
    title: "陪伴发生在日常，而不是聊天框里",
    subtitle: "机器人优先反馈，眼镜补充信息，手机在后台完成计算。",
    kind: "solo",
  },
  {
    kicker: "05 · 虚拟生活",
    title: "当用户离开，宠物的生活仍在继续",
    subtitle: "更接近《动物森友会》的长期经营，而不是一次性对话。",
    kind: "life",
  },
  {
    kicker: "06 · 虚实联动",
    title: "现实中的每个动作，都能改变虚拟世界",
    subtitle: "触摸、工作、运动和实体道具，成为共同生活的输入。",
    kind: "loop",
  },
  {
    kicker: "07 · 多人多机",
    title: "宠物成为人与人之间的新社交媒介",
    subtitle: "从聚会主持，到宠物拜访、组队、送礼与异地互动。",
    kind: "social",
  },
  {
    kicker: "08 · 私有与共享",
    title: "共享一场游戏，不等于共享整个人生",
    subtitle: "私人记忆留在各自 AgentOS，公共服务器只保存房间所需状态。",
    kind: "privacy",
  },
  {
    kicker: "09 · ¥1000 原型",
    title: "用有限硬件，完成完整核心体验",
    subtitle: "预算投入优先服务于陪伴感、可玩性与虚实联动。",
    kind: "prototype",
  },
  {
    kicker: "10 · 技术路径",
    title: "四个核心模块，避免“框架拼盘”",
    subtitle: "每层只有一个权威来源，事件与状态边界清晰。",
    kind: "stack",
  },
  {
    kicker: "11 · 迭代路线",
    title: "先成为好玩的伙伴，再成长为自主机器人",
    subtitle: "每一步都有独立用户价值，也为下一阶段保留接口。",
    kind: "roadmap",
  },
  {
    kicker: "附录 A · 端侧边界",
    title: "谁负责思考，谁负责出现",
    kind: "boundary",
  },
  {
    kicker: "附录 B · 预算梯度",
    title: "预算升级，首先增加可玩性",
    kind: "budgets",
  },
  {
    kicker: "附录 C · 开源选型",
    title: "少而明确，比堆叠框架更可控",
    kind: "opensource",
  },
];

const Arrow = ({ direction }: { direction: "left" | "right" }) => (
  <span aria-hidden="true">{direction === "left" ? "←" : "→"}</span>
);

function SlideContent({ slide }: { slide: Slide }) {
  switch (slide.kind) {
    case "cover":
      return (
        <div className="cover-grid">
          <div className="cover-copy">
            <p className="eyebrow">{slide.kicker}</p>
            <h1>{slide.title}</h1>
            <p className="cover-sub">{slide.subtitle}</p>
            <div className="cover-line">
              私人 AgentOS 的实体化身与空间世界
            </div>
          </div>
          <div className="hero-orbit" aria-label="系统核心关系示意">
            <div className="orbit orbit-a" />
            <div className="orbit orbit-b" />
            <div className="hero-core">
              <span>PRIVATE</span>
              <strong>AgentOS</strong>
              <small>PERSONAL DIGITAL SELF</small>
            </div>
            <div className="satellite sat-robot">机器人<br /><b>现实化身</b></div>
            <div className="satellite sat-glasses">XREAL<br /><b>空间入口</b></div>
            <div className="satellite sat-phone">手机<br /><b>近场计算</b></div>
          </div>
        </div>
      );
    case "problem":
      return (
        <SlideFrame slide={slide}>
          <div className="problem-grid">
            {[
              ["手机 AI", "知道很多，却被困在应用与通知中"],
              ["传统桌宠", "有可爱外形，却缺少长期记忆与行动能力"],
              ["AR 应用", "拥有空间画面，却缺少持续的情感角色"],
              ["线上社交", "能连接远方，却无法共享现实中的陪伴"],
            ].map(([label, copy], index) => (
              <article className="problem-item" key={label}>
                <span>0{index + 1}</span>
                <h3>{label}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
          <p className="takeaway">缺少的不是又一个入口，而是一个贯穿生活的“存在”。</p>
        </SlideFrame>
      );
    case "thesis":
      return (
        <SlideFrame slide={slide}>
          <div className="thesis-map">
            <div className="human-node">人<br /><small>现实生活</small></div>
            <div className="bridge bridge-left">授权 · 记忆 · 目标</div>
            <div className="agent-node">
              <span>唯一核心</span>
              AgentOS
              <small>电子世界中的个人分身</small>
            </div>
            <div className="bridge bridge-right">人格 · 决策 · 状态</div>
            <div className="robot-node">机器人<br /><small>最高优先级反馈实体</small></div>
            <div className="world-band">
              <b>XREAL</b>
              <span>让用户看见机器人生活的虚拟世界</span>
            </div>
          </div>
        </SlideFrame>
      );
    case "roles":
      return (
        <SlideFrame slide={slide}>
          <div className="roles-line">
            {[
              ["AgentOS", "人格、记忆、计划", "CORE"],
              ["机器人", "表达、感知、行动", "BODY"],
              ["手机", "计算、连接、渲染", "HUB"],
              ["眼镜", "空间世界、通知", "VIEW"],
              ["电脑", "工作、学习、创作", "EXEC"],
            ].map(([name, detail, code], index) => (
              <div className="role" key={name}>
                <span>{code}</span>
                <strong>{name}</strong>
                <p>{detail}</p>
                {index < 4 && <i>→</i>}
              </div>
            ))}
          </div>
          <div className="role-rule">
            <strong>反馈原则</strong>
            <span>机器人负责“被感知”</span>
            <span>眼镜负责“被看见”</span>
            <span>手机与电脑负责“把事做完”</span>
          </div>
        </SlideFrame>
      );
    case "solo":
      return (
        <SlideFrame slide={slide}>
          <div className="scene-layout">
            <div className="scene-story">
              <span className="time">09:30</span>
              <h3>用户开始工作</h3>
              <p>机器人进入专注状态；眼镜侧边显示任务；电脑 Agent 执行复杂工作。</p>
              <span className="time">11:15</span>
              <h3>任务完成</h3>
              <p>机器人首先抬头庆祝；眼镜给出摘要；用户决定是否打开电脑查看详情。</p>
            </div>
            <div className="scene-capabilities">
              {["日程与消息", "个人事项处理", "工作学习联动", "健康监督", "智能家居", "情感陪伴", "教育引导", "低视角拍摄"].map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </div>
        </SlideFrame>
      );
    case "life":
      return (
        <SlideFrame slide={slide}>
          <div className="life-cycle">
            {[
              ["清晨", "醒来 · 整理房间"],
              ["白天", "种植 · 工作 · 旅行"],
              ["相遇", "聊天 · 收礼 · 游戏"],
              ["夜晚", "复盘 · 写日记 · 成长"],
            ].map(([time, action], i) => (
              <div className="life-stop" key={time}>
                <span>{i + 1}</span>
                <strong>{time}</strong>
                <p>{action}</p>
              </div>
            ))}
            <div className="life-center">
              <b>持续状态</b>
              <span>心情</span><span>精力</span><span>关系</span><span>收藏</span>
            </div>
          </div>
          <p className="takeaway">用户回来时，听到的是“我今天经历了什么”，而不是“有什么可以帮你”。</p>
        </SlideFrame>
      );
    case "loop":
      return (
        <SlideFrame slide={slide}>
          <div className="loop-track">
            {[
              ["现实输入", "触摸 / 工作 / 运动 / 卡片"],
              ["AgentOS", "理解意义并更新共同状态"],
              ["实体反馈", "表情 / 灯光 / 声音 / 移动"],
              ["AR 反馈", "动画 / 家园 / 道具 / 任务"],
            ].map(([label, text], i) => (
              <div className="loop-step" key={label}>
                <span>0{i + 1}</span>
                <strong>{label}</strong>
                <p>{text}</p>
              </div>
            ))}
          </div>
          <div className="example-strip">
            <b>例</b>
            用户完成专注任务
            <i>→</i>
            机器人庆祝
            <i>→</i>
            虚拟家园获得新家具
          </div>
        </SlideFrame>
      );
    case "social":
      return (
        <SlideFrame slide={slide}>
          <div className="social-modes">
            {[
              ["多人一机", "机器人主持聚会，眼镜显示私人信息"],
              ["多人多机", "每只宠物代表主人，组队、送礼与对战"],
              ["异地同场", "实体机器人本地反馈，AR宠物跨空间出现"],
            ].map(([title, text], i) => (
              <article key={title}>
                <span className="mode-no">MODE 0{i + 1}</span>
                <div className={`mode-visual mode-${i + 1}`}>
                  <i /><i /><i />
                </div>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
          <p className="takeaway">宠物既是主持人，也是每位用户在共同世界中的社交代理。</p>
        </SlideFrame>
      );
    case "privacy":
      return (
        <SlideFrame slide={slide}>
          <div className="privacy-split">
            <section>
              <span>PRIVATE</span>
              <h3>私人 AgentOS</h3>
              <p>完整对话、日程、健康、工作学习、宠物日记与真实关系。</p>
              <b>用户拥有 · 本地优先 · 可撤回授权</b>
            </section>
            <div className="privacy-gate">
              <i>只分享必要信息</i>
              <strong>→</strong>
              <small>公开身份卡<br />当局状态<br />游戏操作</small>
            </div>
            <section className="shared">
              <span>SHARED</span>
              <h3>公共房间</h3>
              <p>参与者、回合、比分、公共动作、临时位置与聚会事件。</p>
              <b>房间有效 · 服务端裁决 · 结束即归档</b>
            </section>
          </div>
        </SlideFrame>
      );
    case "prototype":
      return (
        <SlideFrame slide={slide}>
          <div className="prototype-layout">
            <div className="robot-silhouette">
              <div className="robot-head">
                <i className="eye left" /><i className="eye right" />
                <span>◡</span>
              </div>
              <div className="robot-base">STACKCHAN</div>
              <div className="wheel left" /><div className="wheel right" />
            </div>
            <div className="prototype-copy">
              <div className="price"><small>机器人本体</small>≈ ¥1,000</div>
              <div className="feature-columns">
                <div><b>实体陪伴</b><span>表情 · 说话 · 触摸 · 转头</span></div>
                <div><b>环境互动</b><span>低视角 · 道具 · 简单移动</span></div>
                <div><b>空间扩展</b><span>AR家园 · 游戏 · 多端同步</span></div>
              </div>
              <p>不追求自主导航；把预算集中在用户每天能看见、听见、摸到和玩到的功能。</p>
            </div>
          </div>
        </SlideFrame>
      );
    case "stack":
      return (
        <SlideFrame slide={slide}>
          <div className="stack-layers">
            <div><span>体验层</span><b>Unity + XREAL</b><p>虚拟生活 · AR游戏 · 空间通知</p></div>
            <div><span>智能层</span><b>私人 AgentOS</b><p>人格 · 记忆 · 任务 · 权限</p></div>
            <div><span>社交层</span><b>Colyseus</b><p>房间 · 权威状态 · 多端同步</p></div>
            <div><span>执行层</span><b>设备协议</b><p>StackChan · 电脑 · 智能家居</p></div>
          </div>
          <div className="stack-rule">状态有唯一来源 · AI不裁决游戏规则 · 实体安全留在本机</div>
        </SlideFrame>
      );
    case "roadmap":
      return (
        <SlideFrame slide={slide}>
          <div className="roadmap">
            {[
              ["NOW", "空间桌宠", "人格、表达、AR家园"],
              ["NEXT", "社交伙伴", "多人游戏、多宠关系"],
              ["LATER", "家庭化身", "跨房间、自主回充"],
              ["VISION", "个人智能生命", "持续学习与现实行动"],
            ].map(([tag, title, text], i) => (
              <div className="roadmap-step" key={tag}>
                <span>{tag}</span>
                <strong>{title}</strong>
                <p>{text}</p>
                <i>{i + 1}</i>
              </div>
            ))}
          </div>
          <div className="closing-statement">
            桌宠是情感载体，游戏是交互载体，AR是空间载体。
            <b>AgentOS 让三者成为同一个“生命”。</b>
          </div>
        </SlideFrame>
      );
    case "boundary":
      return (
        <SlideFrame slide={slide}>
          <div className="boundary-table">
            {[
              ["AgentOS", "决定", "人格、记忆、计划、权限、虚拟生活"],
              ["StackChan", "出现", "表情、声音、触摸、动作、简单移动"],
              ["手机 / Beam Pro", "运行", "语音视觉、Unity、游戏、设备连接"],
              ["XREAL", "呈现", "空间世界、通知、虚实叠加"],
              ["电脑", "执行", "办公、学习、创作、编程"],
              ["公共服务器", "同步", "房间、回合、比分、公共事件"],
            ].map(([name, verb, detail]) => (
              <div className="boundary-row" key={name}>
                <strong>{name}</strong><b>{verb}</b><span>{detail}</span>
              </div>
            ))}
          </div>
        </SlideFrame>
      );
    case "budgets":
      return (
        <SlideFrame slide={slide}>
          <div className="budget-table">
            <div className="budget-row header">
              <span>版本</span><span>用户感受</span><span>增加的可玩性</span><span>定位</span>
            </div>
            {[
              ["≤ ¥200", "能说话的电子桌宠", "语音、表情、基础养成", "概念验证"],
              ["¥350–500", "会表达的互动桌宠", "转头、触摸、灯光动作", "陪伴验证"],
              ["≈ ¥1,000", "会移动的空间伙伴", "低视角、实体道具、AR联动", "产品原型"],
              ["最全方案", "自主生活的机器人化身", "跨房间、回充、现实自主活动", "长期愿景"],
            ].map((row, index) => (
              <div className={`budget-row ${index === 2 ? "focus" : ""}`} key={row[0]}>
                {row.map((cell) => <span key={cell}>{cell}</span>)}
              </div>
            ))}
          </div>
        </SlideFrame>
      );
    case "opensource":
      return (
        <SlideFrame slide={slide}>
          <div className="decision-grid">
            <section className="adopt">
              <span>采用</span>
              <b>Unity + XREAL SDK</b>
              <b>StackChan 开发体系</b>
              <b>AgentScope + 单一记忆系统</b>
              <b>Colyseus + WebSocket</b>
            </section>
            <section className="reference">
              <span>参考</span>
              <b>N.E.K.O. 陪伴与记忆</b>
              <b>Kai 9000 移动端交互</b>
              <b>OpenAgents 社交协议</b>
            </section>
            <section className="later">
              <span>后置</span>
              <b>BuckyOS 分布式个人云</b>
              <b>AD4M 去中心化身份</b>
              <b>rivet agentOS 隔离执行</b>
            </section>
          </div>
          <p className="takeaway">原则：一个职责只保留一个核心框架，缺口明确后再引入新依赖。</p>
        </SlideFrame>
      );
  }
}

function SlideFrame({
  slide,
  children,
}: {
  slide: Slide;
  children: React.ReactNode;
}) {
  return (
    <div className="slide-frame">
      <header>
        <p className="eyebrow">{slide.kicker}</p>
        <h2>{slide.title}</h2>
        {slide.subtitle && <p className="slide-subtitle">{slide.subtitle}</p>}
      </header>
      <div className="slide-body">{children}</div>
    </div>
  );
}

export default function Home() {
  const [index, setIndex] = useState(0);
  const touchStart = useRef<number | null>(null);
  const total = slides.length;

  const go = useCallback(
    (next: number) => setIndex(Math.max(0, Math.min(total - 1, next))),
    [total]
  );

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (["ArrowRight", "PageDown", " ", "Enter"].includes(event.key)) {
        event.preventDefault();
        go(index + 1);
      }
      if (["ArrowLeft", "PageUp", "Backspace"].includes(event.key)) {
        event.preventDefault();
        go(index - 1);
      }
      if (event.key === "Home") go(0);
      if (event.key === "End") go(total - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, index, total]);

  const dots = useMemo(
    () =>
      slides.map((slide, i) => (
        <button
          key={slide.title}
          className={i === index ? "active" : ""}
          onClick={() => go(i)}
          aria-label={`前往第 ${i + 1} 页：${slide.title}`}
          title={`${i + 1}. ${slide.title}`}
        />
      )),
    [go, index]
  );

  const fullscreen = async () => {
    if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
    else await document.exitFullscreen();
  };

  return (
    <main
      className="deck"
      onTouchStart={(event) => {
        touchStart.current = event.touches[0]?.clientX ?? null;
      }}
      onTouchEnd={(event) => {
        if (touchStart.current == null) return;
        const delta = event.changedTouches[0].clientX - touchStart.current;
        if (Math.abs(delta) > 50) go(index + (delta < 0 ? 1 : -1));
        touchStart.current = null;
      }}
    >
      <section className={`slide slide-${slides[index].kind}`} aria-live="polite">
        <SlideContent slide={slides[index]} />
      </section>

      <nav className="deck-nav" aria-label="演示文稿导航">
        <button onClick={() => go(index - 1)} disabled={index === 0} aria-label="上一页">
          <Arrow direction="left" />
        </button>
        <div className="dot-nav">{dots}</div>
        <button onClick={() => go(index + 1)} disabled={index === total - 1} aria-label="下一页">
          <Arrow direction="right" />
        </button>
      </nav>

      <div className="slide-count">
        <b>{String(index + 1).padStart(2, "0")}</b>
        <span>/ {String(total).padStart(2, "0")}</span>
      </div>

      <button className="fullscreen" onClick={fullscreen} aria-label="切换全屏" title="全屏">
        ⛶
      </button>
      <div className="progress" style={{ width: `${((index + 1) / total) * 100}%` }} />
    </main>
  );
}

import React, { useState, useEffect, useRef} from "react";
import "./App.css";
import WardrobePage from './WardrobePage';


const questions = [
  { title: "Как тебя зовут?", field: "name" },
  { title: "Сколько тебе лет?", field: "age" },
  {
    title: "Как бы ты описала свой тип фигуры?",
    field: "figura",
    hint: (
      <>
      <strong>Например:</strong> Яблоко (O), Треугольник (A), Перевернутый треугольник (V),<br />
      Прямоугольник (H), «Песочные часы» (X)<br /><br />
      Если не уверена — ничего страшного!<br /><br />
      Этот бот поможет:{" "}
      <a href="https://t.me/figuralnabot" target="_blank" rel="noopener noreferrer">@figuralnabot</a>
    </>
    ),
  },
  {
    title: "Какой у тебя цветотип?",
    field: "cvetotip",
    hint: (
      <>
        <strong>Например:</strong> тёплая весна, холодное лето
        <br /><br />
        Если не уверена — ничего страшного!
        <br /><br />
        Этот бот поможет:{" "}
        <a href="https://t.me/chrommabot" target="_blank" rel="noopener noreferrer">
          @chrommabot
        </a>
      </>
    ),
  },
  { title: "Чем ты занимаешься? Есть ли дресс-код?", field: "rod_zanyatii" },
  {
    title: "Какой стиль одежды тебе ближе всего?",
    field: "predpochtenia_v_stile",
    hint: (
      <>
        <strong>Например:</strong>
        <br />• повседневный (casual)<br />• классика или офисный стиль<br />• спорт-шик<br />• бохо<br />• минимализм<br />• романтичный<br />• пока не знаю, хочу понять
      </>
    ),
  },
  {
    title: "Хочешь что-то изменить в стиле или ищешь вдохновение?",
    field: "change",
    hint: (
      <>
        <strong>Например:</strong>
        <br />• Хочу выглядеть более женственно<br />• Хочется обновить гардероб<br />• Не уверена, но чувствую, что нужно что-то новое<br />• Просто хочется понять, что мне подходит
      </>
    ),
  },
  {
    title: "Какие части тела тебе хочется подчеркнуть?",
    field: "like_zone",
    hint:(
      <>
      <strong>Например:</strong> Талия и ключицы.<br />
      Если не знаешь — так и напиши: не знаю.
      </>
    ),
  },
  {
    title: "Какие зоны ты предпочла бы скрыть?",
    field: "dislike_zone",
    hint:(
      <>
      <strong>Например:</strong> живот и бёдра. <br/>
      Если не знаешь — так и напиши: не знаю.
      </>
    ),
  },
];

export default function App() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({});
  const [animate, setAnimate] = useState(true);
  const [tgId, setTgId] = useState(null);
  const [existingProfile, setExistingProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);
  const [viewing, setViewing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [viewingWardrobe, setViewingWardrobe] = useState(false);
  const wardrobeRef = useRef(null);



  const handleEditProfile = () => {
  setEditForm(existingProfile || {});
  setEditing(true);
};
  const handleSaveEditedProfile = () => {
  fetch("https://lipolo.ru/webhook/anketa_save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ telegram_id: tgId, ...editForm }),
  })
    .then(() => {
      alert("Анкета обновлена!");
      setExistingProfile(editForm);
      setEditing(false);
    })
    .catch(() => alert("Ошибка при сохранении изменений"));
};



  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const tg_id = urlParams.get("tg_id");
    if (tg_id) {
      setTgId(tg_id);
      fetch("https://lipolo.ru/webhook/anketa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telegram_id: tg_id }),
      })
        .then(res => res.json())
        .then(data => {
          const firstProfile = Array.isArray(data) ? data[0] : null;
          setExistingProfile(firstProfile || null);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
  if (viewingWardrobe) {
    window.scrollTo({ top: 0, behavior: "auto" });
  }
}, [viewingWardrobe]);



  const handleChange = (e) => {
    setForm({ ...form, [questions[step].field]: e.target.value });
  };

  const handleNext = () => {
    setAnimate(false);
    setTimeout(() => {
      setAnimate(true);
      if (step < questions.length - 1) {
        setStep(step + 1);
      } else {
        fetch("https://lipolo.ru/webhook/anketa_save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ telegram_id: tgId, ...form }),
        })
          .then(async () => {
            alert("Анкета сохранена!\n\nМожешь закрыть эту страницу.");

            // Отправить сообщение с кнопками (локация / не отправлять)
            await fetch("https://api.telegram.org/bot7774871818:AAHsonb6alqc3QOnjiLrrnyRSUISCvT9OXg/sendMessage", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                chat_id: tgId,
                text: `📍 Чтобы мои советы были по-настоящему полезными, важно знать, в каком климате ты живёшь.

Это поможет учитывать сезон и подбирать одежду, которая будет комфортной в твоей погоде 🌦

👇 Пожалуйста, нажми на кнопку ниже и отправь свою геолокацию:

📌 Не хочешь делиться локацией? Всё в порядке!

👗 Если позже захочешь, чтобы я составила образы — пришли мне текущие погодные условия, и я подберу луки под них.`,
                reply_markup: {
                  keyboard: [
                    [
                      { text: "📍 Отправить локацию", request_location: true },
                      { text: "🚫 Не отправлять локацию" }
                    ]
                  ],
                  resize_keyboard: true,
                  one_time_keyboard: true
                }
              })
            });


            setStarted(false);
            setExistingProfile({ name: form.name });
          })
          .catch(() => alert("Ошибка при сохранении анкеты"));
      }
    }, 120);
  };

  const handleBack = () => {
    setAnimate(false);
    setTimeout(() => {
      setAnimate(true);
      if (step > 0) setStep(step - 1);
    }, 120);
  };

  const handleCancel = () => {
    if (confirm("Вы точно хотите отменить заполнение анкеты?")) {
      setForm({});
      setStep(0);
      setStarted(false);
    }
  };

  const handleStart = () => {
    setForm({});
    setStep(0);
    setStarted(true);
  };

  const handleViewProfile = () => {
    setViewing(true);
  };

  const { title, hint, field } = questions[step];
  const progress = ((step + 1) / questions.length) * 100;
  if (!tgId) {
  return <div className="app">Доступ запрещен</div>;
}

  if (loading) return <div className="app">Загрузка...</div>;

  if (viewingWardrobe && existingProfile?.telegram_id) {
  return (
    <div className="app">
      <WardrobePage
        telegramId={existingProfile.telegram_id}
        access={existingProfile.access}
        scrollRef={wardrobeRef}
        onBack={() => {
          setViewingWardrobe(false);
        }}
      />
    </div>
  );
}

  if (!started && !viewing) {
  return (
    <div className="app">
      <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
        <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
          <img src="/vite.svg" alt="logo" className="logo-img" />
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
          <div className="progress-bar" style={{ flex: 1, maxWidth: 220, margin: "0 auto" }}>
            <div className="progress" style={{ width: `0%` }} />
          </div>
        </div>

        <div style={{ fontSize: "1.4rem", marginBottom: "1rem", textAlign: "center", color: "#7E4A57" }}>
          {existingProfile?.name ? `Привет, ${existingProfile.name}!` : "Добро пожаловать!"}
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
            justifyContent: "center",
            alignItems: "stretch",
            width: "100%",
            maxWidth: 320,
            margin: "0 auto",
          }}
        >
          <div className="buttons" style={{ marginTop: "1.5rem" }}>
            {!existingProfile || !existingProfile.name ? (
              <button onClick={handleStart} className="next">
                Заполнить анкету
              </button>
            ) : (
              <>
                <button onClick={handleViewProfile} className="next">
                  Профиль
                </button>
                {existingProfile.access === "full" && (
                  <button onClick={() => setViewingWardrobe(true)} className="next">
                    Гардероб
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
  if (editing && existingProfile) {
  return (
    <div className="app">
      <div className="card">
        <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
          <img src="/vite.svg" alt="logo" className="logo-img" />
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
          <div className="progress-bar" style={{ flex: 1, maxWidth: 220, margin: "0 auto" }}>
            <div className="progress" style={{ width: `100%` }} />
          </div>
        </div>
        <h2 style={{ marginBottom: '1rem', textAlign: "center" }}>Редактировать профиль</h2>
        <form
          onSubmit={e => {
            e.preventDefault();
            handleSaveEditedProfile(); // твоя функция сохранения
          }}
          style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem', marginBottom: '1.5rem' }}
        >
          {questions.map(q => (
            <div
              key={q.field}
              style={{
                background: "#f7f8fa",
                borderRadius: "10px",
                padding: "12px 14px",
                boxShadow: "0 1px 2px rgba(0,0,0,0.03)",
                border: "1px solid #ececec",
                display: "flex",
                flexDirection: "column",
                gap: "0.3rem"
              }}
            >
              <label style={{ fontWeight: 600, fontSize: "1.04rem", color: "#222" }}>
                {q.title}
              </label>
              <input
                type="text"
                value={editForm[q.field] || ""}
                onChange={e => setEditForm({ ...editForm, [q.field]: e.target.value })}
                placeholder="Введите значение..."
                style={{
                  width: "100%",
                  padding: "8px",
                  fontSize: "1rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                  background: "#fff"
                }}
              />
            </div>
          ))}
          <div className="buttons" style={{ marginTop: "1.5rem" }}>
            <button type="button" className="cancel" onClick={() => setEditing(false)}>
              Назад
            </button>
            <button type="submit" className="next">
              Сохранить изменения
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
  if (viewing && existingProfile && existingProfile.name) {
  return (
    <div className="app">
      <div className="card scrollable-card">
        <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
          <img src="/vite.svg" alt="logo" className="logo-img" />
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
          <div className="progress-bar" style={{ flex: 1, maxWidth: 220, margin: "0 auto" }}>
            <div className="progress" style={{ width: `100%` }} />
          </div>
        </div>
        <h2 style={{ marginBottom: '1rem', textAlign: "center", color: "#7E4A57" }}>Твой профиль</h2>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          {questions.map(q => (
            <div className="profile-block" key={q.field}>
              <div style={{
                fontWeight: 700,
                fontSize: "1.08rem",
                color: "#FFFFFF",
                marginBottom: 2
              }}>
                {q.title}
              </div>
              <div className="answer-from-db">
                {existingProfile[q.field] || <span style={{ color: '#bbb' }}>—</span>}
              </div>
            </div>
          ))}
        </div>
        <div className="buttons" style={{ marginTop: '1.5rem' }}>
          <button className="cancel" onClick={() => setViewing(false)}>Назад</button>
          <button className="next" onClick={handleEditProfile}>Изменить</button>
        </div>
      </div>
    </div>
  );
}
  return (
    <div className="app">
      <div className={`card ${animate ? "fade-in" : "fade-out"}`}>
        <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
          <img src="/vite.svg" alt="logo" className="logo-img" />
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.7rem" }}>
          <div className="progress-bar" style={{ flex: 1, maxWidth: 220, margin: "0 auto" }}>
            <div className="progress" style={{ width: `${progress}%` }} />
          </div>
        </div>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
          <p className="question">{title}</p>
          {hint && (
            <div className="hint" style={{ marginBottom: "1rem", fontSize: "0.95rem", color: "#333" }}>
              {hint}
            </div>
          )}
          <div className="input-wrap">
            <input
              type="text"
              value={form[field] || ""}
              onChange={handleChange}
              placeholder="Введите ответ..."
              autoFocus
            />
          </div>
        </div>
        <div className="buttons">
          {step > 0 && (
            <button className="back" onClick={handleBack}>
              Назад
            </button>
          )}
          <button className="cancel" onClick={handleCancel}>
            Отменить
          </button>
          <button className="next" onClick={handleNext} disabled={!form[field] || !form[field].trim()}>
            {step === questions.length - 1 ? "Сохранить" : "Далее"}
          </button>
        </div>
      </div>
      <style>{`
        .fade-in {
          animation: fadeInCard 0.35s cubic-bezier(.4,0,.2,1);
        }
        .fade-out {
          animation: fadeOutCard 0.15s cubic-bezier(.4,0,.2,1);
        }
        @keyframes fadeInCard {
          from { opacity: 0; transform: translateY(16px) scale(0.98); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes fadeOutCard {
          from { opacity: 1; transform: translateY(0) scale(1); }
          to { opacity: 0; transform: translateY(16px) scale(0.98); }
        }
      `}</style>
    </div>
  );
}

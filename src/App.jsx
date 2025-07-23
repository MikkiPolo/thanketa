import React, { useState, useEffect } from "react";
import "./App.css";

const questions = [
  { title: "Как тебя зовут?", field: "name" },
  { title: "Сколько тебе лет?", field: "age" },
  {
    title: "Как бы ты описала свой тип фигуры?",
    field: "figura",
    hint: (
      <>
        Например: Яблоко (O), Треугольник (A), Перевернутый треугольник (V), Прямоугольник (H), «Песочные часы» (X)
        <br />
        Если не уверена — ничего страшного!
        <br />
        Этот бот поможет:{" "}
        <a href="https://t.me/figuralnabot" target="_blank" rel="noopener noreferrer">
          @figuralnabot
        </a>
      </>
    ),
  },
  {
    title: "Какой у тебя цветотип?",
    field: "cvetotip",
    hint: (
      <>
        Например: тёплая весна, холодное лето
        <br />
        Если не уверена — ничего страшного!
        <br />
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
        Например:
        <br />• повседневный (casual)<br />• классика или офисный стиль<br />• спорт-шик<br />• бохо<br />• минимализм<br />• романтичный<br />• пока не знаю, хочу понять
      </>
    ),
  },
  {
    title: "Хочешь что-то изменить в стиле или ищешь вдохновение?",
    field: "change",
    hint: (
      <>
        Например:
        <br />• Хочу выглядеть более женственно<br />• Хочется обновить гардероб<br />• Не уверена, но чувствую, что нужно что-то новое<br />• Просто хочется понять, что мне подходит
      </>
    ),
  },
  {
    title: "Какие части тела тебе хочется подчеркнуть?",
    field: "like_zone",
    hint: "Например: Талия и ключицы. Если не знаешь — так и напиши: не знаю.",
  },
  {
    title: "Какие зоны ты предпочла бы скрыть?",
    field: "dislike_zone",
    hint: "Например: живот и бёдра. Если не знаешь — так и напиши: не знаю.",
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
        fetch("https://lipolo.ru/webhook-test/anketa_save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ telegram_id: tgId, ...form }),
        })
          .then(() => {
            alert("Анкета сохранена!");
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

  if (loading) return <div className="app">Загрузка...</div>;

  if (!started && !viewing) {
    return (
      <div className="app">
        <div className="card">
          <div style={{ fontSize: "1.4rem", marginBottom: "1rem" }}>
            {existingProfile?.name ? `Привет, ${existingProfile.name}!` : "Добро пожаловать!"}
          </div>
          <div style={{ display: "flex", gap: "1rem" }}>
            {!existingProfile && (
              <button onClick={handleStart} className="next">
                Заполнить анкету
              </button>
            )}
            {existingProfile && (
              <button onClick={handleViewProfile} className="next">
                Просмотреть анкету
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }
  if (viewing && existingProfile) {
  return (
    <div className="app">
      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Твоя анкета</h2>
        <ul style={{ textAlign: 'left', fontSize: '1rem', lineHeight: '1.6' }}>
          {questions.map(q => (
            <li key={q.field}><strong>{q.title}</strong>: {existingProfile[q.field] || '—'}</li>
          ))}
        </ul>
        <div className="buttons" style={{ marginTop: '1.5rem' }}>
          <button className="cancel" onClick={() => setViewing(false)}>Назад</button>
          <button className="next" onClick={handleStart}>Изменить анкету</button>
        </div>
      </div>
    </div>
  );
  if (editing && existingProfile) {
  return (
    <div className="app">
      <div className="card">
        <h2 style={{ marginBottom: "1rem" }}>Редактировать анкету</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSaveEditedProfile();
          }}
          style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
        >
          {questions.map((q) => (
            <div key={q.field}>
              <label style={{ fontWeight: "bold", marginBottom: 4, display: "block" }}>
                {q.title}
              </label>
              <input
                type="text"
                value={editForm[q.field] || ""}
                onChange={(e) => setEditForm({ ...editForm, [q.field]: e.target.value })}
                placeholder="Введите значение..."
                style={{
                  width: "100%",
                  padding: "8px",
                  fontSize: "1rem",
                  borderRadius: "6px",
                  border: "1px solid #ccc",
                }}
              />
            </div>
          ))}
          <div className="buttons" style={{ marginTop: "1.5rem", display: "flex", gap: "1rem" }}>
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

}
  return (
    <div className="app">
      <div className={`card ${animate ? "fade-in" : "fade-out"}`}>
        <div className="logo" style={{ marginTop: "0.5rem", marginBottom: "0.7rem" }}>
          <img src="/vite.svg" alt="logo" style={{ width: 36, height: 36 }} />
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
          <button className="next" onClick={handleNext}>
            Далее
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

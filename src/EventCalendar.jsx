import React, { useState, useEffect } from 'react';

const EventCalendar = ({ onEventSelect }) => {
  const [events, setEvents] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [showEventForm, setShowEventForm] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    date: '',
    time: '',
    dressCode: '',
    weather: ''
  });

  // Генерируем календарь на месяц
  const generateCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());

    const calendar = [];
    const current = new Date(startDate);

    while (current <= lastDay || calendar.length < 42) {
      calendar.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }

    return calendar;
  };

  const calendar = generateCalendar();

  const addEvent = () => {
    if (!newEvent.title || !newEvent.date) return;

    const event = {
      id: Date.now(),
      ...newEvent,
      createdAt: new Date().toISOString()
    };

    setEvents([...events, event]);
    setNewEvent({
      title: '',
      description: '',
      date: '',
      time: '',
      dressCode: '',
      weather: ''
    });
    setShowEventForm(false);
  };

  const deleteEvent = (eventId) => {
    setEvents(events.filter(event => event.id !== eventId));
  };

  const getEventsForDate = (date) => {
    return events.filter(event => {
      const eventDate = new Date(event.date);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short'
    });
  };

  const isToday = (date) => {
    return date.toDateString() === new Date().toDateString();
  };

  const isCurrentMonth = (date) => {
    return date.getMonth() === currentDate.getMonth();
  };

  const isSelected = (date) => {
    return selectedDate && date.toDateString() === selectedDate.toDateString();
  };

  const handleDateClick = (date) => {
    setSelectedDate(date);
    const dayEvents = getEventsForDate(date);
    if (onEventSelect) {
      onEventSelect(date, dayEvents);
    }
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  return (
    <div className="event-calendar">
      <div className="calendar-header">
        <button onClick={prevMonth} className="calendar-nav-btn">‹</button>
        <h3>
          {currentDate.toLocaleDateString('ru-RU', { 
            month: 'long', 
            year: 'numeric' 
          })}
        </h3>
        <button onClick={nextMonth} className="calendar-nav-btn">›</button>
      </div>

      <div className="calendar-grid">
        <div className="calendar-weekdays">
          {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map(day => (
            <div key={day} className="weekday">{day}</div>
          ))}
        </div>

        <div className="calendar-days">
          {calendar.map((date, index) => {
            const dayEvents = getEventsForDate(date);
            const hasEvents = dayEvents.length > 0;

            return (
              <div
                key={index}
                className={`calendar-day ${!isCurrentMonth(date) ? 'other-month' : ''} 
                           ${isToday(date) ? 'today' : ''} 
                           ${isSelected(date) ? 'selected' : ''}
                           ${hasEvents ? 'has-events' : ''}`}
                onClick={() => handleDateClick(date)}
              >
                <span className="day-number">{date.getDate()}</span>
                {hasEvents && (
                  <div className="event-indicator">
                    {dayEvents.length > 1 ? `${dayEvents.length}` : '•'}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="calendar-actions">
        <button 
          className="add-event-btn"
          onClick={() => setShowEventForm(true)}
        >
          + Добавить событие
        </button>
      </div>

      {showEventForm && (
        <div className="event-form-overlay">
          <div className="event-form">
            <h4>Новое событие</h4>
            <div className="form-group">
              <label>Название:</label>
              <input
                type="text"
                value={newEvent.title}
                onChange={(e) => setNewEvent({...newEvent, title: e.target.value})}
                placeholder="Встреча, праздник..."
              />
            </div>
            <div className="form-group">
              <label>Описание:</label>
              <textarea
                value={newEvent.description}
                onChange={(e) => setNewEvent({...newEvent, description: e.target.value})}
                placeholder="Детали события..."
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Дата:</label>
                <input
                  type="date"
                  value={newEvent.date}
                  onChange={(e) => setNewEvent({...newEvent, date: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Время:</label>
                <input
                  type="time"
                  value={newEvent.time}
                  onChange={(e) => setNewEvent({...newEvent, time: e.target.value})}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Дресс-код:</label>
              <input
                type="text"
                value={newEvent.dressCode}
                onChange={(e) => setNewEvent({...newEvent, dressCode: e.target.value})}
                placeholder="Деловой, кэжуал, вечерний..."
              />
            </div>
            <div className="form-group">
              <label>Погода:</label>
              <input
                type="text"
                value={newEvent.weather}
                onChange={(e) => setNewEvent({...newEvent, weather: e.target.value})}
                placeholder="Тепло, холодно, дождь..."
              />
            </div>
            <div className="form-actions">
              <button onClick={() => setShowEventForm(false)} className="cancel-btn">
                Отмена
              </button>
              <button onClick={addEvent} className="save-btn">
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedDate && (
        <div className="selected-date-events">
          <h4>События на {formatDate(selectedDate)}</h4>
          {getEventsForDate(selectedDate).length === 0 ? (
            <p>Нет событий на этот день</p>
          ) : (
            <div className="events-list">
              {getEventsForDate(selectedDate).map(event => (
                <div key={event.id} className="event-item">
                  <div className="event-header">
                    <h5>{event.title}</h5>
                    <button 
                      onClick={() => deleteEvent(event.id)}
                      className="delete-event-btn"
                    >
                      ✕
                    </button>
                  </div>
                  {event.description && <p>{event.description}</p>}
                  {event.time && <p>Время: {event.time}</p>}
                  {event.dressCode && <p>Дресс-код: {event.dressCode}</p>}
                  {event.weather && <p>Погода: {event.weather}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EventCalendar; 
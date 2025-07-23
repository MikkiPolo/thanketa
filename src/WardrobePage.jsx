import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

const WardrobePage = ({ telegramId, access, onBack }) => {
  const [wardrobe, setWardrobe] = useState([]);
  const [editingRow, setEditingRow] = useState(null);
  const [editedData, setEditedData] = useState({});
  

  const hasFetched = useRef(false);

  const fetchWardrobe = () => {
  setWardrobe([]); // <== добавь эту строку
  axios.post('https://lipolo.ru/webhook/getwardrobe', { telegram_id: telegramId })
    .then(res => {
      const cleaned = res.data.filter(item => item && item.id);
      setWardrobe(cleaned);
    })
    .catch(err => console.error('Error fetching wardrobe:', err));
};

useEffect(() => {
  console.log('Wardrobe effect', { telegramId, access });
  if (!hasFetched.current && telegramId && access === 'full') {
    hasFetched.current = true;
    axios.post('https://lipolo.ru/webhook/getwardrobe', { telegram_id: telegramId })
      .then(res => {
        const cleaned = res.data.filter(item => item && item.id);
        console.log('Fetched wardrobe:', cleaned);
        setWardrobe(cleaned);
      })
      .catch(err => console.error('Error fetching wardrobe:', err));
  }
}, [telegramId, access]);

  const handleEdit = (id, item) => {
    setEditingRow(id);
    setEditedData(item);
  };

  const handleChange = (field, value) => {
    setEditedData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async (row) => {
    try {
      await axios.post('https://lipolo.ru/webhook/wardrobe_safe', {
        ...editedData,
        id: row.id,
        telegram_id: row.telegram_id,
      });
      setWardrobe(prev =>
        prev.map(item => item.id === row.id ? { ...item, ...editedData } : item)
      );
      setEditingRow(null);
      setEditedData({});
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  const handleDelete = async (id) => {
  const confirmed = window.confirm("Точно хотите удалить эту вещь?");
  if (!confirmed) return;

  try {
    const response = await axios.post('https://lipolo.ru/webhook/wardrobe_del', { id });
    if (response.status === 200) {
      fetchWardrobe();
      if (editingRow === id) {
        setEditingRow(null);
        setEditedData({});
      }
    }
  } catch (err) {
    console.error("Ошибка при удалении:", err);
  }
};


 return (
  <div className="card">
    <div className="wardrobe-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
     <h2 style={{ margin: 0 }}>Твой гардероб</h2>
     <button className="back-btn" onClick={onBack}>← Назад</button>
    </div>
    <div className="wardrobe-list">
      {wardrobe.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#777', padding: '1rem' }}>
          Гардероб пуст
        </div>
      ) : (
        wardrobe
         .filter(item => item && item.id && item.category)
         .map(item => (
          <div key={item.id} className="wardrobe-item-block">
            {editingRow === item.id ? (
              <>
                <div>
                  <strong>Категория:</strong>{' '}
                  <input
                    type="text"
                    value={editedData.category || ''}
                    onChange={e => handleChange('category', e.target.value)}
                  />
                </div>
                <div>
                  <strong>Сезонность:</strong>{' '}
                  <input
                    type="text"
                    value={editedData.season || ''}
                    onChange={e => handleChange('season', e.target.value)}
                  />
                </div>
                <div>
                  <strong>Описание:</strong>{' '}
                  <input
                    type="text"
                    value={editedData.description || ''}
                    onChange={e => handleChange('description', e.target.value)}
                  />
                </div>
                <button
                  className="wardrobe-save-btn"
                  disabled={
                    !editedData.category ||
                    !editedData.season ||
                    !editedData.description
                  }
                  onClick={() => handleSave(item)}
                >
                  Сохранить
                </button>
              </>
            ) : (
              <>
                <div><strong>Категория:</strong> {item.category}</div>
                <div><strong>Сезонность:</strong> {item.season}</div>
                <div><strong>Описание:</strong> {item.description}</div>
                <div className="wardrobe-buttons">
                 <button
                  className="wardrobe-edit-btn"
                  onClick={() => handleEdit(item.id, item)}
                >
                  Изменить
                 </button>
                 <button
                  className="wardrobe-delete-btn"
                  onClick={() => handleDelete(item.id)}
                >
                  Удалить
                 </button>
              </div>
             </>
            )}
          </div>
        ))
      )}
    </div>
  </div>
);
}
export default WardrobePage;
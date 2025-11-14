import React, { useState, useRef, useEffect } from 'react';
import { Send, Image as ImageIcon, X } from 'lucide-react';
import { API_ENDPOINTS, BACKEND_URL } from './config';
import './App.css';

const ChatPage = ({ telegramId }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(() => {
    // Загружаем threadId из localStorage при инициализации
    const savedThreadId = localStorage.getItem(`chat_thread_${telegramId}`);
    return savedThreadId || null;
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Прокрутка к последнему сообщению
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Загружаем историю сообщений при монтировании, если есть threadId
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!threadId || !telegramId) return;
      
      try {
        const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.CHAT_HISTORY}?thread_id=${threadId}&telegram_id=${telegramId}`);
        
        if (!response.ok) {
          return;
        }
        
        const data = await response.json();
        if (data.messages && Array.isArray(data.messages)) {
          // Преобразуем сообщения из формата OpenAI в формат компонента
          const formattedMessages = data.messages.map((msg, idx) => ({
            id: Date.now() - (data.messages.length - idx) * 1000, // Уникальные ID
            role: msg.role,
            text: msg.content || '',
            image: msg.image_url || null
          }));
          setMessages(formattedMessages);
        }
      } catch (error) {
        console.error('❌ Ошибка загрузки истории:', error);
      }
    };
    
    loadChatHistory();
  }, [threadId, telegramId]);

  // Автоматическое изменение высоты textarea
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Сбрасываем высоту, чтобы получить правильный scrollHeight
      textarea.style.height = 'auto';
      // Устанавливаем новую высоту на основе содержимого
      const newHeight = Math.min(textarea.scrollHeight, 120); // max-height из CSS
      textarea.style.height = `${newHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [inputMessage]);

  // Обработка выбора изображения
  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);
      
      // Проверяем, является ли файл HEIC/HEIF
      const fileName = file.name.toLowerCase();
      const isHeic = fileName.endsWith('.heic') || fileName.endsWith('.heif');
      
      if (isHeic) {
        // Для HEIC файлов конвертируем на бэкенде для превью
        // Показываем placeholder сразу, пока идет конвертация
        const placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5IRUlDIEluYWdlPC90ZXh0Pjwvc3ZnPg==';
        setImagePreview(placeholder);
        
        try {
          // Отправляем файл на бэкенд для конвертации
          const formData = new FormData();
          formData.append('image', file);
          
          const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.CONVERT_HEIC_PREVIEW}`, {
            method: 'POST',
            body: formData
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const result = await response.json();
          
          if (result.success && result.preview) {
            setImagePreview(result.preview);
          } else {
            throw new Error(result.error || 'Не удалось получить превью');
          }
        } catch (error) {
          console.error('Ошибка получения превью HEIC:', error);
          // Оставляем placeholder, если конвертация не удалась
        }
      } else {
        // Для обычных форматов используем стандартный FileReader
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreview(e.target.result);
        };
        reader.readAsDataURL(file);
      }
    }
  };

  // Удаление выбранного изображения
  const handleRemoveImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Отправка сообщения
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !selectedImage) return;
    if (isLoading) return;

    // Сохраняем данные перед очисткой
    const messageText = inputMessage;
    const imageFile = selectedImage;
    const previewUrl = imagePreview;

    // СРАЗУ очищаем превью и выбранное изображение при нажатии на отправку
    handleRemoveImage();
    setInputMessage('');
    
    // Сбрасываем высоту textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    setIsLoading(true);

    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: messageText,
      image: previewUrl
    };

    setMessages(prev => [...prev, userMessage]);

    // Отменяем предыдущий запрос, если есть
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const formData = new FormData();
      formData.append('telegram_id', telegramId);
      formData.append('message', messageText || '');
      if (threadId) {
        formData.append('thread_id', threadId);
      }
      if (imageFile) {
        formData.append('image', imageFile);
      }
      formData.append('include_wardrobe', 'false'); // По умолчанию не включаем гардероб

      const response = await fetch(`${BACKEND_URL}${API_ENDPOINTS.CHAT_STYLE}`, {
        method: 'POST',
        body: formData,
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Добавляем сообщение ассистента с индикатором "думает"
      const assistantMessageId = Date.now() + 1;
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant',
        text: '',
        isThinking: true, // Показываем индикатор "думает"
        isStreaming: false
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Читаем stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'thread_id') {
                setThreadId(data.thread_id);
                // Сохраняем threadId в localStorage для восстановления при следующем открытии
                localStorage.setItem(`chat_thread_${telegramId}`, data.thread_id);
              } else if (data.type === 'text_delta') {
                // Убираем индикатор "думает" при первом тексте и добавляем новый текст
                setMessages(prev => {
                  return prev.map((msg, idx) => {
                    // Находим последнее сообщение ассистента
                    if (idx === prev.length - 1 && msg.role === 'assistant' && msg.id === assistantMessageId) {
                      const updatedMsg = { ...msg };
                      if (updatedMsg.isThinking) {
                        updatedMsg.isThinking = false;
                        updatedMsg.isStreaming = true;
                      }
                      // Добавляем только новый текст (не дублируем)
                      if (data.text) {
                        updatedMsg.text = (updatedMsg.text || '') + data.text;
                      }
                      return updatedMsg;
                    }
                    return msg;
                  });
                });
              } else if (data.type === 'done' || data.type === 'message_completed') {
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === assistantMessageId) {
                    lastMessage.isThinking = false;
                    lastMessage.isStreaming = false;
                  }
                  return newMessages;
                });
              } else if (data.type === 'error') {
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === assistantMessageId) {
                    lastMessage.isThinking = false;
                    lastMessage.isStreaming = false;
                    if (!lastMessage.text) {
                      lastMessage.text = '❌ Ошибка при получении ответа. Попробуйте еще раз.';
                    }
                  }
                  return newMessages;
                });
                throw new Error(data.error);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }

      // Завершаем streaming
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === assistantMessageId) {
          lastMessage.isThinking = false;
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });

    } catch (error) {
      if (error.name === 'AbortError') {
        // Request aborted
        return;
      }
      console.error('Error sending message:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === assistantMessageId) {
          lastMessage.isThinking = false;
          lastMessage.isStreaming = false;
          if (!lastMessage.text) {
            lastMessage.text = '❌ Ошибка при отправке сообщения. Попробуйте еще раз.';
          }
        } else {
          newMessages.push({
            id: Date.now() + 2,
            role: 'assistant',
            text: '❌ Ошибка при отправке сообщения. Попробуйте еще раз.',
            isStreaming: false,
            isThinking: false
          });
        }
        return newMessages;
      });
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Обработка Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Рендеринг markdown (жирный текст, ссылки, списки, переносы строк)
  const renderMarkdown = (text) => {
    if (!text) return '';
    
    // Разбиваем на строки для обработки
    const lines = text.split('\n');
    const elements = [];
    
    lines.forEach((line, lineIndex) => {
      if (line.trim() === '') {
        elements.push(<br key={`br-${lineIndex}`} />);
        return;
      }
      
      // Обрабатываем markdown ссылки [text](url) и обычные URL
      const processLine = (lineText) => {
        const parts = [];
        let lastIndex = 0;
        let keyIndex = 0;
        
        // Сначала обрабатываем markdown ссылки [text](url)
        const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        let match;
        const matches = [];
        
        // Собираем все совпадения
        while ((match = markdownLinkRegex.exec(lineText)) !== null) {
          matches.push({
            index: match.index,
            length: match[0].length,
            text: match[1],
            url: match[2]
          });
        }
        
        // Обрабатываем жирный текст **text**
        const boldRegex = /\*\*(.+?)\*\*/g;
        const boldMatches = [];
        while ((match = boldRegex.exec(lineText)) !== null) {
          boldMatches.push({
            index: match.index,
            length: match[0].length,
            text: match[1]
          });
        }
        
        // Объединяем все совпадения и сортируем по индексу
        const allMatches = [
          ...matches.map(m => ({ ...m, type: 'link' })),
          ...boldMatches.map(m => ({ ...m, type: 'bold' }))
        ].sort((a, b) => a.index - b.index);
        
        // Обрабатываем совпадения
        for (const match of allMatches) {
          // Текст до совпадения
          if (match.index > lastIndex) {
            const beforeText = lineText.substring(lastIndex, match.index);
            // Проверяем, есть ли в этом тексте обычные URL
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            let urlMatch;
            let urlLastIndex = 0;
            while ((urlMatch = urlRegex.exec(beforeText)) !== null) {
              if (urlMatch.index > urlLastIndex) {
                parts.push(
                  <span key={`text-${lineIndex}-${keyIndex++}`}>
                    {beforeText.substring(urlLastIndex, urlMatch.index)}
                  </span>
                );
              }
              parts.push(
                <a 
                  key={`url-${lineIndex}-${keyIndex++}`}
                  href={urlMatch[1]} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="chat-link"
                >
                  {urlMatch[1]}
                </a>
              );
              urlLastIndex = urlMatch.index + urlMatch[0].length;
            }
            if (urlLastIndex < beforeText.length) {
              parts.push(
                <span key={`text-${lineIndex}-${keyIndex++}`}>
                  {beforeText.substring(urlLastIndex)}
                </span>
              );
            }
          }
          
          // Обрабатываем совпадение
          if (match.type === 'link') {
            parts.push(
              <a 
                key={`link-${lineIndex}-${keyIndex++}`}
                href={match.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="chat-link"
              >
                {match.text}
              </a>
            );
          } else if (match.type === 'bold') {
            parts.push(
              <strong key={`bold-${lineIndex}-${keyIndex++}`}>
                {match.text}
              </strong>
            );
          }
          
          lastIndex = match.index + match.length;
        }
        
        // Остаток строки
        if (lastIndex < lineText.length) {
          const remainingText = lineText.substring(lastIndex);
          // Проверяем, есть ли в остатке обычные URL
          const urlRegex = /(https?:\/\/[^\s]+)/g;
          let urlMatch;
          let urlLastIndex = 0;
          while ((urlMatch = urlRegex.exec(remainingText)) !== null) {
            if (urlMatch.index > urlLastIndex) {
              parts.push(
                <span key={`text-end-${lineIndex}-${keyIndex++}`}>
                  {remainingText.substring(urlLastIndex, urlMatch.index)}
                </span>
              );
            }
            parts.push(
              <a 
                key={`url-end-${lineIndex}-${keyIndex++}`}
                href={urlMatch[1]} 
                target="_blank" 
                rel="noopener noreferrer"
                className="chat-link"
              >
                {urlMatch[1]}
              </a>
            );
            urlLastIndex = urlMatch.index + urlMatch[0].length;
          }
          if (urlLastIndex < remainingText.length) {
            parts.push(
              <span key={`text-end-${lineIndex}-${keyIndex++}`}>
                {remainingText.substring(urlLastIndex)}
              </span>
            );
          }
        }
        
        // Если нет совпадений, проверяем на обычные URL
        if (parts.length === 0) {
          const urlRegex = /(https?:\/\/[^\s]+)/g;
          let urlMatch;
          let urlLastIndex = 0;
          while ((urlMatch = urlRegex.exec(lineText)) !== null) {
            if (urlMatch.index > urlLastIndex) {
              parts.push(
                <span key={`plain-${lineIndex}-${keyIndex++}`}>
                  {lineText.substring(urlLastIndex, urlMatch.index)}
                </span>
              );
            }
            parts.push(
              <a 
                key={`url-plain-${lineIndex}-${keyIndex++}`}
                href={urlMatch[1]} 
                target="_blank" 
                rel="noopener noreferrer"
                className="chat-link"
              >
                {urlMatch[1]}
              </a>
            );
            urlLastIndex = urlMatch.index + urlMatch[0].length;
          }
          if (urlLastIndex < lineText.length) {
            parts.push(
              <span key={`plain-end-${lineIndex}-${keyIndex++}`}>
                {lineText.substring(urlLastIndex)}
              </span>
            );
          }
          if (parts.length === 0) {
            parts.push(<span key={`plain-${lineIndex}`}>{lineText}</span>);
          }
        }
        
        return parts;
      };
      
      const parts = processLine(line);
      
      elements.push(
        <div key={`line-${lineIndex}`} className="chat-message-line">
          {parts}
        </div>
      );
    });
    
    return elements;
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>Чат с GLAMORA (beta)</h2>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Задавай вопросы или отправляй фото для консультации</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`chat-message ${message.role}`}>
            {message.image && (
              <div className="chat-message-image">
                <img src={message.image} alt="User upload" />
              </div>
            )}
            {message.isThinking && (
              <div className="chat-message-text">
                <span className="thinking-indicator">
                  <span className="thinking-dot"></span>
                  <span className="thinking-dot"></span>
                  <span className="thinking-dot"></span>
                </span>
              </div>
            )}
            {message.text && (
              <div className="chat-message-text">
                {renderMarkdown(message.text)}
                {message.isStreaming && !message.isThinking && <span className="typing-indicator">▋</span>}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {imagePreview && (
        <div className="chat-image-preview" style={{ display: 'block' }}>
          <img 
            src={imagePreview} 
            alt="Preview" 
            onLoad={() => {
              // Preview image loaded
            }}
            onError={(e) => {
              console.error('❌ Ошибка загрузки превью:', e);
              console.error('❌ src:', imagePreview?.substring(0, 100));
            }}
          />
          <button onClick={handleRemoveImage} className="chat-remove-image">
            <X size={20} />
          </button>
        </div>
      )}

      <div className="chat-input-container">
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          onChange={handleImageSelect}
          style={{ display: 'none' }}
        />
        <button
          className="chat-image-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <ImageIcon size={22} />
        </button>
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={inputMessage}
          onChange={(e) => {
            setInputMessage(e.target.value);
            adjustTextareaHeight();
          }}
          onKeyPress={handleKeyPress}
          placeholder="Напишите сообщение..."
          rows={1}
          disabled={isLoading}
        />
        <button
          className="chat-send-button"
          onClick={handleSendMessage}
          disabled={isLoading || (!inputMessage.trim() && !selectedImage)}
        >
          <Send size={22} />
        </button>
      </div>
    </div>
  );
};

export default ChatPage;

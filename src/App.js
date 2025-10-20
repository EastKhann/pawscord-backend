import React, { useState, useEffect, useRef } from 'react';

// Python Backend WebSocket adresi
// Daphne varsayılan olarak 8000 portunda çalışır.
const WS_URL = 'ws://127.0.0.1:8000/ws/chat/'; 

function App() {
  // Mesajları saklamak için durum (state)
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  
  // WebSocket nesnesini saklamak için useRef kullanıyoruz (component yeniden render olsa bile nesne kaybolmaz)
  const ws = useRef(null); 
  
  // Mesaj kutusunun altını otomatik kaydırmak için referans
  const messagesEndRef = useRef(null); 

  // Mesajlar listesini en alta kaydırma fonksiyonu
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // Mesajlar durumu (state) her değiştiğinde scroll fonksiyonunu çağır
  useEffect(scrollToBottom, [messages]); 

  // Bileşen (Component) yüklendiğinde WebSocket bağlantısını kur
  useEffect(() => {
    // WebSocket bağlantısını başlat
    ws.current = new WebSocket(WS_URL);

    // 1. Bağlantı Başarılı Olduğunda (Python sunucusuna bağlandı)
    ws.current.onopen = () => {
      setMessages((prev) => [
        ...prev, 
        { type: 'system', text: 'Sohbet sunucusuna başarılı bir şekilde bağlanıldı.' }
      ]);
    };

    // 2. Sunucudan Mesaj Geldiğinde
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Gelen mesajı (username ve message) listeye ekle
      setMessages((prev) => [
        ...prev, 
        { 
          type: 'chat', 
          username: data.username, 
          text: data.message 
        }
      ]);
    };

    // 3. Bağlantı Kapandığında
    ws.current.onclose = () => {
      setMessages((prev) => [
        ...prev, 
        { type: 'system', text: 'Bağlantı kesildi. Lütfen Python sunucusunun çalıştığından emin olun.' }
      ]);
    };

    // Temizleme fonksiyonu: Bileşen kaldırıldığında bağlantıyı kapat
    return () => {
      // Eğer bağlantı hala açıksa kapat
      if (ws.current.readyState === WebSocket.OPEN) {
          ws.current.close();
      }
    };
  }, []); // Boş dizi, bu kodun sadece bir kez (ilk yüklemede) çalışmasını sağlar

  // Mesaj Gönderme İşlevi
  const sendMessage = (e) => {
    e.preventDefault();
    
    // Mesaj boşsa veya bağlantı hazır değilse gönderme
    if (messageInput.trim() === '' || ws.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Mesajı JSON formatında sunucuya gönder (Python Consumer'ın beklediği format)
    ws.current.send(JSON.stringify({
      'message': messageInput.trim()
    }));

    // Mesaj kutusunu temizle
    setMessageInput('');
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Gerçek Zamanlı Sohbet (Lobby)</h1>
      
      {/* Mesaj Görüntüleme Alanı */}
      <div style={styles.messageBox}>
        {messages.map((msg, index) => (
          <div 
            key={index} 
            style={
              msg.type === 'system' ? styles.systemMessage : styles.chatMessage
            }
          >
            {msg.type === 'chat' && <strong>{msg.username}: </strong>}
            {msg.text}
          </div>
        ))}
        {/* Scroll noktası: Yeni mesaj geldiğinde buraya kaydırılacak */}
        <div ref={messagesEndRef} /> 
      </div>
      
      {/* Mesaj Gönderme Formu */}
      <form onSubmit={sendMessage} style={styles.inputForm}>
        <input
          type="text"
          value={messageInput}
          onChange={(e) => setMessageInput(e.target.value)}
          placeholder="Mesajınızı buraya yazın..."
          style={styles.inputField}
        />
        <button type="submit" style={styles.sendButton}>Gönder</button>
      </form>
      
      <p style={styles.status}>Backend Durumu: {
          ws.current && ws.current.readyState === WebSocket.OPEN 
            ? 'BAĞLI' 
            : 'BAĞLANIYOR / KAPALI'
      }</p>
    </div>
  );
}

// Basit CSS stilleri (Inline Styles)
const styles = {
    container: {
        maxWidth: '800px',
        margin: '0 auto',
        padding: '20px',
        fontFamily: 'Arial, sans-serif'
    },
    header: {
        textAlign: 'center',
        borderBottom: '2px solid #3f51b5',
        paddingBottom: '10px'
    },
    messageBox: {
        height: '400px',
        border: '1px solid #ccc',
        overflowY: 'auto',
        padding: '10px',
        marginBottom: '15px',
        backgroundColor: '#f9f9f9'
    },
    chatMessage: {
        padding: '5px 0',
        borderBottom: '1px dotted #eee'
    },
    systemMessage: {
        padding: '5px 0',
        color: 'gray',
        fontStyle: 'italic',
        textAlign: 'center'
    },
    inputForm: {
        display: 'flex',
    },
    inputField: {
        flexGrow: 1,
        padding: '10px',
        border: '1px solid #3f51b5',
        borderRadius: '4px 0 0 4px',
        fontSize: '16px'
    },
    sendButton: {
        padding: '10px 20px',
        backgroundColor: '#3f51b5',
        color: 'white',
        border: 'none',
        borderRadius: '0 4px 4px 0',
        cursor: 'pointer'
    },
    status: {
        textAlign: 'center',
        marginTop: '10px',
        color: '#3f51b5'
    }
};

export default App;
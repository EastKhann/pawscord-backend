import React, { useState, useEffect, useRef, useCallback } from 'react';
import RoomList from './RoomList';
import ChatUserList from './ChatUserList';

// --- DİNAMİK URL YAPILANDIRMASI ---
const NGROK_HOST = 'pseudostudiously-reflexional-clara.ngrok-free.dev'; // Kendi NGROK adresinizi buraya yazın
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_HOST = isLocal ? 'localhost:8000' : NGROK_HOST;
const API_PROTOCOL = isLocal ? 'http' : 'https';
const WS_PROTOCOL = isLocal ? 'ws' : 'wss';

const MESSAGE_HISTORY_URL = `${API_PROTOCOL}://${API_HOST}/api/messages/history/`;
const ROOM_OPTIONS = ['genel', 'teknoloji', 'oyun', 'spor', 'dehsetpurna'];
const ICE_SERVERS = [{ urls: 'stun:stun.l.google.com:19302' }];


const formatTimestamp = (timestamp) => {
    const messageDate = new Date(timestamp);
    const now = new Date();
    const isToday = messageDate.getDate() === now.getDate() && messageDate.getMonth() === now.getMonth() && messageDate.getFullYear() === now.getFullYear();
    if (isToday) {
        return messageDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
        return messageDate.toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    }
};

function App() {
    // STATE VE REF TANIMLAMALARI
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [username, setUsername] = useState('');
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [roomName, setRoomName] = useState(ROOM_OPTIONS[0]);
    const [isConnected, setIsConnected] = useState(false);
    const [newMessages, setNewMessages] = useState({});
    const [voiceUsers, setVoiceUsers] = useState({});
    const [isInVoiceChat, setIsInVoiceChat] = useState(false);
    const [typingUsers, setTypingUsers] = useState([]);
    const [remoteVolumes, setRemoteVolumes] = useState({});
    const [currentVoiceRoom, setCurrentVoiceRoom] = useState(null);
    const [chatUsers, setChatUsers] = useState([]);
    const [pendingJoinRoom, setPendingJoinRoom] = useState(null);

    const ws = useRef(null);
    const statusWsRef = useRef(null);
    const messagesEndRef = useRef(null);
    const voiceWsRef = useRef(null);
    const peerConnectionsRef = useRef({});
    const localStreamRef = useRef(null);
    const typingTimeoutRef = useRef(null);

    // YARDIMCI VE WEBRTC FONKSİYONLARI
    const scrollToBottom = () => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); };
    const sendSignal = (signal) => { if (voiceWsRef.current && voiceWsRef.current.readyState === WebSocket.OPEN) { voiceWsRef.current.send(JSON.stringify(signal)); } };
    const setRemoteVolume = useCallback((partnerUsername, volume) => { setRemoteVolumes(prev => ({ ...prev, [partnerUsername]: volume })); const audioEl = document.getElementById(`audio-${partnerUsername}`); if (audioEl) { audioEl.volume = volume / 100; } }, []);
    const handleRemoteStream = (partnerUsername, stream) => { let audioEl = document.getElementById(`audio-${partnerUsername}`); if (!audioEl) { audioEl = document.createElement('audio'); audioEl.id = `audio-${partnerUsername}`; audioEl.autoplay = true; document.body.appendChild(audioEl); } audioEl.srcObject = stream; const currentVolume = remoteVolumes[partnerUsername] || 100; audioEl.volume = currentVolume / 100; };
    const createPeerConnection = (partnerUsername, stream) => { const peerConnection = new RTCPeerConnection({ iceServers: ICE_SERVERS }); stream.getTracks().forEach(track => { peerConnection.addTrack(track, stream); }); peerConnection.ontrack = (event) => { handleRemoteStream(partnerUsername, event.streams[0]); }; peerConnection.onicecandidate = (event) => { if (event.candidate) { sendSignal({ type: 'candidate', candidate: event.candidate, receiver_username: partnerUsername, sender_username: username, }); } }; peerConnectionsRef.current[partnerUsername] = peerConnection; return peerConnection; };
    const leaveVoiceChat = useCallback(() => { if (localStreamRef.current) { localStreamRef.current.getTracks().forEach(track => track.stop()); localStreamRef.current = null; } const currentVoiceRoomUrl = voiceWsRef.current?.url.match(/voice\/([^/]+)/)?.[1]; if (voiceWsRef.current && voiceWsRef.current.readyState === WebSocket.OPEN) { sendSignal({ type: 'leave', sender_username: username, room: currentVoiceRoomUrl }); } if (voiceWsRef.current) { voiceWsRef.current.close(1000, 'manual_leave'); voiceWsRef.current = null; } else { setIsInVoiceChat(false); } Object.values(peerConnectionsRef.current).forEach(pc => pc.close()); peerConnectionsRef.current = {}; setCurrentVoiceRoom(null); }, [username]);
    const joinVoiceChat = useCallback(async (roomSlug) => { if (voiceWsRef.current && voiceWsRef.current.readyState === WebSocket.OPEN) { return; } let stream; try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); localStreamRef.current = stream; } catch (error) { alert("Mikrofon izni gereklidir."); return; } const encodedUsername = encodeURIComponent(username); const voiceWs = new WebSocket(`${WS_PROTOCOL}://${API_HOST}/ws/voice/${roomSlug}/?username=${encodedUsername}`); voiceWsRef.current = voiceWs; voiceWs.onerror = () => { setIsInVoiceChat(false); setCurrentVoiceRoom(null); }; voiceWs.onopen = () => { setIsInVoiceChat(true); setCurrentVoiceRoom(roomSlug); sendSignal({ type: 'join', sender_username: username, room: roomSlug }); }; voiceWs.onmessage = async (event) => { const signal = JSON.parse(event.data); const sender = signal.sender_username; const type = signal.type; if (type === 'voice_state_update' || sender === username) return; let pc = peerConnectionsRef.current[sender]; if (!pc) { if (type !== 'offer' && type !== 'join') return; pc = createPeerConnection(sender, stream); } if (signal.type === 'join') { const offer = await pc.createOffer(); await pc.setLocalDescription(offer); sendSignal({ type: 'offer', sdp: pc.localDescription, receiver_username: sender, sender_username: username }); } else if (signal.type === 'offer') { if (pc.signalingState !== 'stable' && pc.signalingState !== 'have-local-pranswer') return; await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp)); const answer = await pc.createAnswer(); await pc.setLocalDescription(answer); sendSignal({ type: 'answer', sdp: pc.localDescription, receiver_username: sender, sender_username: username }); } else if (signal.type === 'answer') { if (pc.signalingState !== 'have-local-offer') return; await pc.setRemoteDescription(new RTCSessionDescription(signal.sdp)); } else if (signal.type === 'candidate') { if (pc.remoteDescription && signal.candidate) { try { await pc.addIceCandidate(new RTCIceCandidate(signal.candidate)); } catch (e) { if (e.name !== 'InvalidStateError') console.error('ICE adayı eklenirken hata:', e); } } } }; voiceWs.onclose = () => { setIsInVoiceChat(false); setCurrentVoiceRoom(null); }; }, [username, leaveVoiceChat]);
    
    // USEEFFECT HOOK'LARI
    useEffect(() => { if (!isInVoiceChat && pendingJoinRoom) { const roomToJoin = pendingJoinRoom; setPendingJoinRoom(null); joinVoiceChat(roomToJoin); } }, [isInVoiceChat, pendingJoinRoom, joinVoiceChat]);
    useEffect(scrollToBottom, [messages]);
    useEffect(() => { const storedUsername = localStorage.getItem('chat_username'); if (storedUsername) { setUsername(storedUsername); setIsAuthenticated(true); } }, []);
    useEffect(() => { if (!isAuthenticated) return; const STATUS_WS_URL = `${WS_PROTOCOL}://${API_HOST}/ws/status/?username=${encodeURIComponent(username)}`; if (statusWsRef.current) { statusWsRef.current.close(1000, 'reconnect'); statusWsRef.current = null; } const newStatusWs = new WebSocket(STATUS_WS_URL); statusWsRef.current = newStatusWs; newStatusWs.onmessage = (event) => { const data = JSON.parse(event.data); if (data.type === 'voice_state_update') { if (data.initial_load) { setVoiceUsers(data.rooms); } else { const roomNameFromSignal = data.room_name; const userList = data.users; setVoiceUsers(prev => ({ ...prev, [roomNameFromSignal]: userList })); } } }; newStatusWs.onclose = () => { console.log("Global Status WS bağlantısı kesildi."); }; newStatusWs.onerror = (error) => { console.error("Global Status WS hatası:", error); }; return () => { if (newStatusWs && newStatusWs.readyState === WebSocket.OPEN) { newStatusWs.close(1000, 'component_cleanup'); } }; }, [isAuthenticated, username]);

    useEffect(() => {
        if (!isAuthenticated) return;
        const encodedUsername = encodeURIComponent(username);
        const DYNAMIC_WS_URL = `${WS_PROTOCOL}://${API_HOST}/ws/chat/${roomName}/?username=${encodedUsername}`;
        if (ws.current) { if (ws.current.readyState === WebSocket.OPEN) { ws.current.send(JSON.stringify({ type: 'typing_stop' })); } ws.current.close(1000, 'room_change'); ws.current = null; }
        setTypingUsers([]); setChatUsers([]); clearTimeout(typingTimeoutRef.current);
        const newWs = new WebSocket(DYNAMIC_WS_URL); ws.current = newWs;
        newWs.onopen = () => { fetch(`${MESSAGE_HISTORY_URL}${roomName}/`).then(res => res.json()).then(data => { const formatted = data.map(m => ({ type: 'chat', ...m, text: m.content })); setMessages([...formatted, { type: 'system', text: `Oda geçmişi yüklendi: ${roomName.toUpperCase()}` }]); }).catch(err => console.error("Geçmiş yüklenemedi:", err)); setIsConnected(true); newWs.send(JSON.stringify({ type: 'mark_read', room: roomName })); setNewMessages(prev => ({ ...prev, [roomName]: false })); };
        newWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_user_list_update') { setChatUsers(data.users); return; }
            if (data.type === 'typing_update') { setTypingUsers(data.users.filter(u => u !== username)); return; }
            if (data.type === 'voice_state_update') return;
            setMessages((prev) => [ ...prev, { type: 'chat', username: data.username, text: data.message, timestamp: data.timestamp } ]);
        };
        newWs.onclose = () => { setIsConnected(false); setTypingUsers([]); setChatUsers([]); };
        newWs.onerror = () => { setIsConnected(false); setTypingUsers([]); setChatUsers([]); };
        return () => { if (newWs && (newWs.readyState === WebSocket.OPEN || newWs.readyState === WebSocket.CONNECTING)) { if (newWs.readyState === WebSocket.OPEN) { newWs.send(JSON.stringify({ type: 'typing_stop' })); } newWs.close(1000, 'component_cleanup'); } clearTimeout(typingTimeoutRef.current); };
    }, [isAuthenticated, roomName, username]);

    // MESAJ GÖNDERME VE YAZIYOR SİNYALİ
    const sendTypingSignal = (type) => { if (ws.current && ws.current.readyState === WebSocket.OPEN) { ws.current.send(JSON.stringify({ type: type })); } };
    const handleMessageInputChange = (e) => { const value = e.target.value; setMessageInput(value); if (!isConnected || !isAuthenticated) return; if (value.length > 0 && !typingTimeoutRef.current) { sendTypingSignal('typing_start'); } clearTimeout(typingTimeoutRef.current); typingTimeoutRef.current = setTimeout(() => { sendTypingSignal('typing_stop'); typingTimeoutRef.current = null; }, 3000); };
    const sendMessage = (e) => { e.preventDefault(); if (!isAuthenticated || messageInput.trim() === '' || !ws.current || ws.current.readyState !== WebSocket.OPEN) return; if (typingTimeoutRef.current) { clearTimeout(typingTimeoutRef.current); typingTimeoutRef.current = null; sendTypingSignal('typing_stop'); } ws.current.send(JSON.stringify({ 'type': 'chat_message', 'message': messageInput.trim(), 'username': username, 'room': roomName })); setMessageInput(''); };
    const typingMessage = typingUsers.length > 0 ? ( typingUsers.length === 1 ? `${typingUsers[0]} yazıyor...` : typingUsers.length > 3 ? `${typingUsers.length} kişi yazıyor...` : `${typingUsers.slice(0, 3).join(', ')} yazıyor...` ) : null;

    return (
        <div style={styles.mainContainer}>
          {!isAuthenticated ? (
            <div style={styles.centeredAuthBox}>
                <div style={styles.authBox}>
                    <h2>Sohbete katılmak için adınızı girin</h2>
                    <form onSubmit={(e) => { e.preventDefault(); if (username.trim()) { setIsAuthenticated(true); localStorage.setItem('chat_username', username.trim()); } }}>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Adınız..." style={{...styles.inputField, width: '100%', marginBottom: '10px'}} required />
                        <button type="submit" style={{...styles.sendButton, width: '100%'}}>Katıl</button>
                    </form>
                </div>
            </div>
          ) : (
            <div style={styles.chatLayout}>
                <div style={styles.sidebarWrapper}>
                    <RoomList
                        roomOptions={ROOM_OPTIONS} currentRoom={roomName}
                        setRoomName={(newRoom) => { if (newRoom === roomName) return; if (ws.current && ws.current.readyState === WebSocket.OPEN) { ws.current.send(JSON.stringify({ type: 'mark_read', room: newRoom })); } setRoomName(newRoom); setMessages([]); setNewMessages(prev => ({ ...prev, [newRoom]: false })); }}
                        isConnected={isConnected} newMessages={newMessages} voiceUsers={voiceUsers} currentUsername={username} isInVoiceChat={isInVoiceChat}
                        currentVoiceRoom={currentVoiceRoom} remoteVolumes={remoteVolumes} setRemoteVolume={setRemoteVolume}
                        joinVoiceChat={(roomSlug) => { if (isInVoiceChat) { setPendingJoinRoom(roomSlug); leaveVoiceChat(); } else { joinVoiceChat(roomSlug); } }}
                        leaveVoiceChat={leaveVoiceChat} />
                </div>
                <div style={styles.mainContent}>
                    <div style={styles.chatArea}>
                        <h1 style={styles.header}># {roomName.toUpperCase()}</h1>
                        <div style={styles.messageBox}>
                            {messages.map((msg, index) => (
                                <div key={index} style={ msg.type === 'system' ? styles.systemMessage : styles.chatMessage }>
                                    {msg.type === 'chat' ? (
                                        <>
                                            <div style={{ float: 'right' }}>
                                                <span style={styles.timestamp}> ({msg.timestamp ? formatTimestamp(msg.timestamp) : 'Şimdi'})</span>
                                            </div>
                                            <strong>{msg.username}: </strong> {msg.text}
                                            <div style={{ clear: 'both' }}></div>
                                        </>
                                    ) : ( msg.text )}
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>
                        {typingMessage && ( <p style={styles.typingStatus}>{typingMessage}</p> )}
                        <form onSubmit={sendMessage} style={styles.inputForm}>
                            <input type="text" value={messageInput} onChange={handleMessageInputChange} placeholder={`Mesajınızı buraya yazın...`} style={styles.inputField} />
                            <button type="submit" style={styles.sendButton} disabled={!isConnected}>Gönder</button>
                        </form>
                        <p style={styles.status}>Backend Durumu: {isConnected ? 'BAĞLI' : 'BAĞLANTI YOK'}</p>
                    </div>
                    <ChatUserList users={chatUsers} />
                </div>
            </div>
          )}
        </div>
    );
}

const styles = {
    mainContainer: { display: 'flex', height: '100vh', backgroundColor: '#36393f', width: '100%', overflow: 'hidden' },
    centeredAuthBox: { display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100vh' },
    chatLayout: { display: 'flex', width: '100%', height: '100vh' },
    sidebarWrapper: { position: 'relative', width: '250px', minWidth: '250px', backgroundColor: '#2f3136', height: '100%', display: 'flex', flexDirection: 'column' },
    mainContent: { display: 'flex', flex: 1, height: '100%' },
    chatArea: { flexGrow: 1, display: 'flex', flexDirection: 'column', padding: '0 20px 20px 20px', backgroundColor: '#36393f', color: '#fff', height: '100%', boxSizing: 'border-box' },
    header: { padding: '20px 0 10px 0', borderBottom: '1px solid #444', marginBottom: '10px', color: '#fff' },
    messageBox: { flexGrow: 1, overflowY: 'auto', paddingRight: '10px', marginBottom: '15px' },
    chatMessage: { padding: '5px 0', borderBottom: '1px dotted #444', wordWrap: 'break-word' },
    systemMessage: { padding: '5px 0', color: '#ccc', fontStyle: 'italic', textAlign: 'center' },
    inputForm: { display: 'flex' },
    inputField: { flexGrow: 1, padding: '10px', border: '1px solid #555', borderRadius: '4px 0 0 4px', fontSize: '16px', backgroundColor: '#444', color: 'white' },
    sendButton: { padding: '10px 20px', backgroundColor: '#5865f2', color: 'white', border: 'none', borderRadius: '0 4px 4px 0', cursor: 'pointer' },
    status: { textAlign: 'center', marginTop: '10px', color: '#5865f2' },
    authBox: { padding: '20px', border: '1px solid #5865f2', textAlign: 'center', backgroundColor: '#2f3136', color: 'white', borderRadius: '8px', boxShadow: '0 0 15px rgba(0,0,0,0.5)' },
    timestamp: { fontSize: '0.75em', color: '#888', marginLeft: '10px' },
    typingStatus: { textAlign: 'left', height: '25px', marginTop: '5px', marginBottom: '5px', color: '#7289da', fontSize: '0.9em', fontWeight: 'bold' },
};

export default App;
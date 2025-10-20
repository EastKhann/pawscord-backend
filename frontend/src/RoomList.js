import React from 'react';
import VoiceUserList from './VoiceUserList';
import logo from './assets/logo.png';
const RoomList = ({
    roomOptions,
    currentRoom,
    setRoomName,
    isConnected,
    isInVoiceChat,
    joinVoiceChat,
    leaveVoiceChat,
    newMessages,
    voiceUsers,
    currentUsername,
    currentVoiceRoom,
    remoteVolumes,
    setRemoteVolume
}) => {
    
    const activeVoiceUsers = voiceUsers && typeof voiceUsers === 'object' ? voiceUsers : {};

    const handleTextRoomChange = (newRoom) => {
        if (newRoom !== currentRoom) {
            setRoomName(newRoom);
        }
    };
    
    const handleVoiceToggle = (roomSlug) => {
        if (isInVoiceChat && roomSlug === currentVoiceRoom) {
            leaveVoiceChat();
            return;
        }
        
        if (isConnected) {
            joinVoiceChat(roomSlug);
        }
    };
    
    // src/RoomList.js dosyasında return kısmını bul ve aşağıdaki gibi değiştir

return (
    <div style={styles.sidebar}>
        {/* Üst Kısım: Metin ve Sesli Sohbet Kanalları */}
        <div style={styles.topSection}> {/* YENİ: Bu div eklendi */}
            {/* BÖLÜM 1: METİN SOHBET KANALLARI */}
            <h3 style={styles.groupHeader}># Metin Sohbet Kanalları</h3>
            {roomOptions.map((room) => {
                const isCurrentTextRoom = room === currentRoom;
                const roomHasNewMessages = newMessages[room];

                return (
                    <div
                        key={room}
                        style={{
                            ...styles.roomItem,
                            backgroundColor: isCurrentTextRoom ? '#444754' : 'transparent',
                            color: isCurrentTextRoom ? 'white' : '#ccc',
                            cursor: isConnected ? 'pointer' : 'default',
                        }}
                        onClick={() => handleTextRoomChange(room)}
                    >
                        # {room.toUpperCase()}
                        {roomHasNewMessages && <span style={styles.newBadge}>!</span>}
                    </div>
                );
            })}

            {/* BÖLÜM 2: SESLİ SOHBET KANALLARI */}
            <h3 style={{...styles.groupHeader, marginTop: '20px'}}>🔊 Sesli Sohbet Kanalları</h3>
            {roomOptions.map((room) => {
                const isCurrentVoiceRoom = currentVoiceRoom === room;
                const usersInThisRoom = activeVoiceUsers[room] || [];
                const userCount = usersInThisRoom.length;
                const shouldShowUserList = userCount > 0;
                
                return (
                    <div key={`voice-${room}`} style={styles.voiceRoomContainer}>
                        <div style={styles.voiceRoomHeader}>
                            <button
                                style={{ ...styles.voiceToggleButton, backgroundColor: isCurrentVoiceRoom ? '#fa4e4e' : '#5865f2' }}
                                onClick={() => handleVoiceToggle(room)}
                                disabled={!isConnected}
                            >
                                🔊 {room.toUpperCase()}
                                {userCount > 0 && ` (${userCount})`}
                                {isCurrentVoiceRoom ? (' (AYRIL)') : (' (Katıl/Geç)')}
                            </button>
                        </div>
                        {shouldShowUserList && (
                            <div style={styles.voiceUserListWrapper}>
                                <VoiceUserList
                                    voiceUsers={activeVoiceUsers}
                                    roomName={room}
                                    currentUsername={currentUsername}
                                    isClientInThisChannel={isCurrentVoiceRoom}
                                    remoteVolumes={remoteVolumes}
                                    setRemoteVolume={setRemoteVolume}
                                />
                            </div>
                        )}
                    </div>
                );
            })}
        </div> {/* topSection'ın sonu */}

        {/* YENİ: Alt Kısım: Logo ve Site Adı */}
        <div style={styles.bottomSection}>
            <div style={styles.logoContainer}>
                <img src={logo} alt="Site Logosu" style={styles.logoImage} />
                <h1 style={styles.logoText}>Pawcord</h1>
            </div>
        </div>

    </div>
);
};

// src/RoomList.js dosyasını açın ve sadece 'styles' objesini aşağıdaki ile değiştirin

// src/RoomList.js dosyasını açın ve sadece 'styles' objesini aşağıdaki ile değiştirin

const styles = {
    // --- DEĞİŞİKLİKLER BU ALANDA ---

    logoContainer: {
        display: 'flex',
        flexDirection: 'column', // YENİ: Öğeleri dikeyde sırala (logo üste, yazı alta)
        alignItems: 'center',    // YENİ: Öğeleri yatayda ortala
        justifyContent: 'center',  // YENİ: Dikeyde de ortala
        padding: '10px 15px',
    },
    logoImage: {
        height: '70px',          // DEĞİŞTİRİLDİ: Boyut belirgin şekilde artırıldı
        width: '70px',           // DEĞİŞTİRİLDİ: Boyut belirgin şekilde artırıldı
        marginBottom: '10px',    // YENİ: Logo ile yazı arasına boşluk koy
    },
    logoText: {
        color: 'white',
        fontSize: '1.2em',       // DEĞİŞTİRİLDİ: Yazı boyutu ayarlandı
        margin: 0,
        fontWeight: 'bold',
    },
    bottomSection: {
        padding: '10px 15px 20px 15px',
        borderTop: '1px solid #444',
        marginTop: 'auto',
    },
    
    // --- BU KISIMDAN AŞAĞISI AYNI KALIYOR ---

    sidebar: {
        width: '250px',
        minHeight: '100vh',
        backgroundColor: '#2f3136',
        color: 'white',
        paddingTop: '10px',
        boxShadow: '2px 0 5px rgba(0,0,0,0.2)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
    },
    topSection: {
        flexGrow: 1,
        overflowY: 'auto', // Eğer oda listesi uzarsa kaydırma çubuğu çıksın
    },
    groupHeader: {
        padding: '5px 15px',
        fontSize: '1em',
        color: '#99aab5',
        marginBottom: '10px',
        fontWeight: 'bold',
        textTransform: 'uppercase',
    },
    voiceRoomHeader: {
        marginBottom: '0',
        padding: '0 15px',
    },
    voiceToggleButton: {
        width: '100%',
        padding: '5px 15px',
        border: 'none',
        borderRadius: '5px',
        color: 'white',
        fontWeight: 'bold',
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
        marginBottom: '0',
    },
    newBadge: {
        float: 'right',
        backgroundColor: 'red',
        color: 'white',
        borderRadius: '50%',
        padding: '2px 6px',
        fontSize: '0.8em',
        marginLeft: '10px',
        fontWeight: 'bold',
    },
    voiceUserListWrapper: {
        padding: '0 15px 5px 15px',
        backgroundColor: '#2f3136',
        borderRadius: '0',
        margin: '0',
    },
    voiceRoomContainer: {
        padding: '0',
        marginBottom: '5px',
        display: 'block',
    },
    roomItem: {
        padding: '8px 15px',
        transition: 'background-color 0.15s, color 0.15s',
        userSelect: 'none',
        borderRadius: '4px',
        margin: '2px 10px',
    },
};

export default RoomList;
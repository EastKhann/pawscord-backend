import React from 'react';

const VoiceUserList = ({ voiceUsers, roomName, currentUsername, remoteVolumes, setRemoteVolume, isClientInThisChannel }) => {

    if (!voiceUsers || typeof voiceUsers !== 'object' || Array.isArray(voiceUsers)) {
        return null;
    }

    const usersInRoom = voiceUsers[roomName] || [];

    if (!Array.isArray(usersInRoom) || usersInRoom.length === 0) {
        return null;
    }

    const handleVolumeChange = (user, event) => {
        const volume = event.target.value;
        setRemoteVolume(user, parseInt(volume, 10));
    };

    return (
        <div style={styles.container}>
            <h4 style={styles.header}>Aktif Kullanıcılar ({usersInRoom.length})</h4>
            <div style={styles.userList}>
                {usersInRoom.map((user) => {
                    // Kendi ses seviyemizi ayarlayamayız (sadece başkalarını).
                    if (user === currentUsername) {
                        return (
                            <div key={user} style={styles.userItem}>
                                <span style={styles.selfUser}>🎤 {user} (Sen)</span>
                            </div>
                        );
                    }
                    
                    const currentVolume = remoteVolumes[user] || 100;

                    // Eğer istemci bu kanalda DEĞİLSE, sadece kullanıcının adını göster.
                    if (!isClientInThisChannel) {
                        return (
                            <div key={user} style={styles.userItem}>
                                <div style={styles.userDisplay}>
                                    <span>🔊 {user}</span>
                                </div>
                            </div>
                        );
                    }

                    // Eğer istemci bu kanaldaysa, ses ayar çubuğuyla birlikte tam listeyi göster.
                    return (
                        <div key={user} style={styles.userItem}>
                            <div style={styles.userDisplay}>
                                <span>🔊 {user}</span>
                            </div>
                            
                            {/* Ses Seviyesi Kaydırıcısı */}
                            <div style={styles.volumeControl}>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={currentVolume}
                                    onChange={(e) => handleVolumeChange(user, e)}
                                    style={styles.volumeSlider}
                                />
                                <span style={styles.volumeText}>{currentVolume}%</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const styles = {
    container: {
        width: '100%',
        backgroundColor: 'transparent',
        color: '#ccc',
        padding: '0',
    },
    header: {
        fontSize: '0.8em',
        padding: '3px 0 0 0',
        marginBottom: '2px',
        color: '#99aab5',
        textTransform: 'uppercase',
    },
    userList: {
        padding: '0',
    },
    userItem: {
        padding: '3px 0',
        fontSize: '0.9em',
        borderBottom: '1px solid #3d3f44',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
    },
    userDisplay: {
        marginBottom: '3px',
    },
    selfUser: {
        color: '#4CAF50',
        fontWeight: 'bold',
    },
    volumeControl: {
        display: 'flex',
        alignItems: 'center',
        width: '100%',
    },
    volumeSlider: {
        flexGrow: 1,
        marginRight: '5px',
        height: '4px',
        cursor: 'pointer',
    },
    volumeText: {
        fontSize: '0.75em',
        minWidth: '35px',
        textAlign: 'right',
        color: '#99aab5',
    }
};
export default VoiceUserList;
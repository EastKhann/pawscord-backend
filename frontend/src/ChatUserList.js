import React from 'react';

const ChatUserList = ({ users }) => {
    if (!users || users.length === 0) {
        return (
            <div style={styles.container}>
                <h3 style={styles.header}>KİMSE YOK</h3>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <h3 style={styles.header}>ODADAKİLER ({users.length})</h3>
            <ul style={styles.userList}>
                {users.map(user => (
                    <li key={user} style={styles.userItem}>
                        {user}
                    </li>
                ))}
            </ul>
        </div>
    );
};

const styles = {
    container: {
        width: '240px',
        minWidth: '240px',
        backgroundColor: '#2f3136',
        color: '#fff',
        padding: '20px 10px',
        borderLeft: '1px solid #444',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        paddingBottom: '10px',
        borderBottom: '1px solid #444',
        marginBottom: '10px',
        color: '#99aab5',
        fontSize: '1em',
        fontWeight: 'bold',
        textTransform: 'uppercase',
    },
    userList: {
        listStyle: 'none',
        padding: 0,
        margin: 0,
        overflowY: 'auto',
    },
    userItem: {
        padding: '8px 10px',
        borderRadius: '4px',
        marginBottom: '5px',
        color: '#dcddde',
        backgroundColor: '#3a3d43',
    },
};

export default ChatUserList;
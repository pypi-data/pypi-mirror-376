/*
 * SPDX-License-Identifier: LGPL-3.0-or-later
 */

// Wait for the DOM to be fully loaded before executing the script
document.addEventListener('DOMContentLoaded', function() {
    // Constants
    // TODO: set this variable only if the variable is not already defined elsewhere (like in the jinja template)
    // const manageUserAPI = '/users/api';

    // DOM Elements
    const userGrid = document.getElementById('user-grid');
    const authFilterButtons = document.querySelectorAll('.auth-filters > .tab-button');
    const adminFilterButtons = document.querySelectorAll('.admin-filters > .tab-button');
    const banFilterButtons = document.querySelectorAll('.ban-filters > .tab-button');

    // Event Listeners
    [authFilterButtons, adminFilterButtons, banFilterButtons].forEach(buttonGroup => {
        buttonGroup.forEach(button => {
            button.addEventListener('click', () => {
                updateActiveFilter(button, buttonGroup);
                fetchAndDisplayUsers();
            });
        });
    });

    // Initial fetch and display of users
    fetchAndDisplayUsers();

    // Filter Functionality
    function updateActiveFilter(clickedButton, buttonGroup) {
        buttonGroup.forEach(btn => btn.classList.remove('active'));
        clickedButton.classList.add('active');
    }

    // User Management Functions
    function fetchAndDisplayUsers() {
        const selectedAuthFilter = document.querySelector('.auth-filters .active')?.getAttribute('filter') || 'all';
        const selectedAdminFilter = document.querySelector('.admin-filters .active')?.getAttribute('filter') || 'all';
        const selectedBanFilter = document.querySelector('.ban-filters .active')?.getAttribute('filter') || 'all';

        jsonReq = JSON.stringify({
            type: 'list-users',
            'auth-filter': selectedAuthFilter,
            'admin-filter': selectedAdminFilter,
            'banned-filter': selectedBanFilter
        });

        console.log(jsonReq);

        fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: jsonReq
        })
        .then(response => response.json())
        .then(users => {
            userGrid.innerHTML = '';
            users.forEach(user => {
                const userElement = createUserElement(user);
                userGrid.appendChild(userElement);
            });
        })
        .catch(error => console.error('Error fetching users:', error));
    }

    function getUser(authMethod, userId) {
        return fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: "get-user", user_auth: authMethod, user_id: userId})
        })
        .then(response => {return response.json()})
        // .then(user => {return user})
        .catch(error => console.error('Error getting user data:', error));
    }

    function createUserElement(user) {
        console.log(user);
        const userElement = document.createElement('div');
        userElement.classList.add('user-item');
        userElement.classList.add('user-card');
        userElement.innerHTML = `
            <h3>${user.realname}</h3>
            <p>Identifer: ${user.ident}</p>
            <p>Authentication method: ${user.auth_method}</p>
            <p>Admin: ${user.admin ? 'Yes' : 'No'}</p>
            <p>Banned: ${!user.is_active ? 'Yes' : 'No'}</p>
            <p>User group: ${user.usergroup}</p>
            <p>Requests: ${user.requests_remaining} / ${user.max_requests}</p>
        `;
        userElement.addEventListener('click', () => showUserModal(user));
        return userElement;
    }

    function showUserModal(user) {
        const modal = document.createElement('div');
        modal.classList.add('modal');
        // make sure authenticator is registered
        registeredAuthMethod(user.auth_method)
        .then(isAuthRegistered => {
            if (isAuthRegistered) {
                modal.innerHTML = `
                    <div id="user-modal" class="modal-content">
                        <h2>User Options: ${user.realname}</h2>
                        <p>Identifier: ${user.auth_method}.${user.ident}</p>
                        <button id="toggle-admin" class="${user.admin ? 'active' : ''}">Toggle Admin Status</button>
                        <button id="toggle-ban" class="${!user.is_active ? 'active' : ''}">Toggle Ban Status</button>
                        <div class="request-adjust">
                            <button id="decrease-requests">-</button>
                            <span>Requests: ${user.requests_remaining}</span>
                            <button id="increase-requests">+</button>
                        </div>
                        <button id="remove-user">Remove User</button>
                        <button id="close-modal">Close</button>
                    </div>
                    `;
    
                    // modal buttons
                    modal.querySelector('#toggle-admin').addEventListener('click', () => {updateUserStatus(user.auth_method, user.ident, 'toggle-admin', !user.admin).then(user => refreshUserModal(modal, user));});
                    modal.querySelector('#toggle-ban').addEventListener('click', () => {updateUserStatus(user.auth_method, user.ident, 'toggle-ban', user.is_active).then(user => refreshUserModal(modal, user));});
                    modal.querySelector('#decrease-requests').addEventListener('click', () => {updateUserRequests(user.auth_method, user.ident, 'remove').then(user => refreshUserModal(modal, user));});
                    modal.querySelector('#increase-requests').addEventListener('click', () => {updateUserRequests(user.auth_method, user.ident, 'add').then(user => refreshUserModal(modal, user));});
                    modal.querySelector('#remove-user').addEventListener('click', () => {removeUser(user.auth_method, user.ident); modal.remove();});
                    modal.querySelector('#close-modal').addEventListener('click', () => modal.remove());
            }
            // if auth method is not registered, make read only
            else {
                modal.innerHTML = `
                    <div id="user-modal" class="modal-content">
                        <h2>User Options: ${user.realname}</h2>
                        <p>NOTE: The authentication method for this user is not registered. All user data listed is read-only.</p>
                        <p>Identifier: ${user.auth_method}.${user.ident}</p>
                        <p>Admin Status: ${!user.admin ? 'Not' : ''} Admin</p>
                        <p>Banned Status: ${user.is_active ? 'Not' : ''} Banned</p>
                        <p>Requests: ${user.requests_remaining}</p>
                        <button id="remove-user">Remove User</button>
                        <button id="close-modal">Close</button>
                    </div>
                    `;
    
                // Remove and Close Buttons
                modal.querySelector('#remove-user').addEventListener('click', () => {removeUser(user.auth_method, user.ident, true); modal.remove();});
                modal.querySelector('#close-modal').addEventListener('click', () => modal.remove());
            }
        })

        document.body.appendChild(modal);

    }

    function registeredAuthMethod(authMethod) {
        return fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: "check-user-auth", user_auth: authMethod})
        })
        .then(response => response.json())
        .then(result => {return result.is_auth_registered})
    }

    function refreshUserModal(modal, user) {
        showUserModal(user);
        modal.remove();
    }


    function updateUserStatus(authMethod, userId, action, new_stat) {
        return fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: action, user_auth: authMethod, user_id: userId, new_status: new_stat })
        })
        .then(response => response.json())
        .then(result => {
            console.log(`User status updated: ${result.response}`);
            fetchAndDisplayUsers();
            return getUser(authMethod, userId);
        })
        .catch(error => console.error('Error updating user status:', error));
    }

    function updateUserRequests(authMethod, userId, action) {
        return fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'update-requests', user_auth: authMethod, user_id: userId, action: action })
        })
        .then(response => response.json())
        .then(result => {
            console.log(`User requests updated: ${result.response}`);
            fetchAndDisplayUsers();
            return getUser(authMethod, userId);
        })
        .catch(error => console.error('Error updating user requests:', error));
    }

    /**
     * Removes a user from the database
     * @param {string} authMethod - the authentication method of the user 
     * @param {string} userId - the ID of the user
     * @param {Boolean} forceRemove - if true, attempts to remove the user without checking if the auth method is registered
     */
    function removeUser(authMethod, userId, forceRemove=false) {
        if (confirm('Are you sure you want to remove this user?')) {
            fetch(manageUserAPI, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'remove-user', user_auth: authMethod, user_id: userId, force_remove: forceRemove })
            })
            .then(response => response.json())
            .then(result => {
                console.log(`User removed: ${result.response}`);
                fetchAndDisplayUsers();
            })
            .catch(error => console.error('Error removing user:', error));
        }
    }

    // New functions that need HTML changes
    
    // Note: This function needs a corresponding HTML button to trigger it
    function fetchUser() {
        // TODO use custom modal dialogs instead of builtins
        const userId = prompt("Enter user ID to fetch:");
        if (userId) {
            fetch(manageUserAPI, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'fetch-user', user_id: userId })
            })
            .then(response => response.json())
            .then(user => {
                console.log('Fetched user:', user);
                // TODO: Display fetched user information
            })
            .catch(error => console.error('Error fetching user:', error));
        }
    }

    // Note: This function needs corresponding HTML buttons to trigger listing and executing the clean-up
    function handleCacheCleanup() {
        fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'list-cleanables' })
        })
        .then(response => response.json())
        .then(cleanableUsers => {
            // TODO: Show the list on the html with a brief list and a button instead of using builtin functions
            console.log('Cleanable users:', cleanableUsers);
            // TODO: Display list of cleanable users
            if (confirm('Are you sure you want to remove these users from the cache?')) {
                executeCacheCleanup();
            }
        })
        .catch(error => console.error('Error listing cleanable users:', error));
    }

    function executeCacheCleanup() {
        fetch(manageUserAPI, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'clean-cache' })
        })
        .then(response => response.json())
        .then(result => {
            console.log('Cache cleanup result:', result);
            fetchAndDisplayUsers();
        })
        .catch(error => console.error('Error cleaning cache:', error));
    }

    // Expose functions that need to be called from HTML
    window.fetchUser = fetchUser;
    window.handleCacheCleanup = handleCacheCleanup;
});
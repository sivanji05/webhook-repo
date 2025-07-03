document.addEventListener('DOMContentLoaded', () => {
    const eventsContainer = document.getElementById('events-container');

    // Function to format the date 
    const formatTimestamp = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', { 
            day: 'numeric', 
            month: 'long', 
            year: 'numeric', 
            hour: 'numeric', 
            minute: '2-digit',
            hour12: true,
            timeZoneName: 'short' 
        });
    };

    // Function to fetch and display events
    const fetchEvents = async () => {
        try {
            const response = await fetch('/events');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const events = await response.json();


             //client-side sorting to ensure proper order
            events.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return dateB - dateA; // newest first
        });

            // Clear previous content
            eventsContainer.innerHTML = ''; 

            if (events.length === 0) {
                eventsContainer.innerHTML = '<p>No recent activity found.</p>';
                return;
            }

            // Create and append event elements
            events.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';

                //  const timestampSpan = `<span class="timestamp">${formatTimestamp(event.timestamp)}</span>`;
                const timestampSpan = `<span class="timestamp">${new Date(event.timestamp).toLocaleString('en-US', { 
                    day: 'numeric', 
                    month: 'long', 
                    year: 'numeric', 
                    hour: 'numeric', 
                    minute: '2-digit',
                    hour12: true,
                    timeZone: 'UTC',
                    timeZoneName: 'short' 
                })}</span>`;
                
                let message = '';
                
                // Format the message based on the action type
                switch (event.action) {
                    case 'PUSH':
                        message = `<span class="author">"${event.author}"</span> pushed to <strong> "${event.to_branch}"</strong>`;
                        break;
                    case 'PULL_REQUEST':
                        message = `<span class="author">"${event.author}"</span> submitted a pull request from <strong>"${event.from_branch}"</strong> to <strong>"${event.to_branch}"</strong>`;
                        break;
                    case 'MERGE':
                        message = `<span class="author">"${event.author}"</span> merged branch <strong>"${event.from_branch}"</strong> into <strong>"${event.to_branch}"</strong>`;
                        break;
                    default:
                        message = 'An unknown action occurred.';
                }

                eventDiv.innerHTML = `${message} ${timestampSpan}`;
                eventsContainer.appendChild(eventDiv);
            });

        } catch (error) {
            console.error('Failed to fetch events:', error);
            eventsContainer.innerHTML = '<p>Error loading events. Please check the console.</p>';
        }
    };

    // Fetch events immediately on page load
    fetchEvents();

    // Then, fetch for events every 15 seconds
    setInterval(fetchEvents, 15000);
});


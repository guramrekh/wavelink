document.addEventListener('DOMContentLoaded', function() {
  
  // --- Auto-dismiss for existing server-rendered flash messages ---
  const existingFlashMessages = document.querySelectorAll('.flash-messages .custom-alert');
  existingFlashMessages.forEach(notification => {
    // Check if it's already visible or being processed to avoid double timeouts
    if (notification.classList.contains('show') && !notification.dataset.hiding) {
        notification.dataset.hiding = 'true'; // Mark as being processed
        setTimeout(() => {
            if (notification.parentNode) { // Check if still in DOM
                notification.classList.remove('show');
                notification.classList.add('hide');
                // Remove the element after the hide animation completes (matches CSS transition)
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300); 
            }
        }, 3000); // 3 seconds
    } else if (!notification.classList.contains('hide') && !notification.dataset.hiding) {
        // If not initially shown by server (e.g. no 'fade show'), make it appear
        notification.offsetHeight; // Trigger reflow
        notification.classList.add('show');
        notification.dataset.hiding = 'true'; // Mark as being processed
        setTimeout(() => {
             if (notification.parentNode) { // Check if still in DOM
                notification.classList.remove('show');
                notification.classList.add('hide');
                setTimeout(() => {
                   if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 3000); // 3 seconds
    }
  });

  // --- Element Selectors ---
  const searchForms = document.querySelectorAll('.song-search-form');
  const searchResultsModal = document.getElementById('search-results-modal');
  const searchResultsContainer = document.getElementById('search-results-container');
  const searchLoading = document.getElementById('search-loading');
  const noResults = document.getElementById('no-results');
  const closeModalBtn = searchResultsModal ? searchResultsModal.querySelector('.close-modal') : null;

  // Basic check if modal elements exist
  if (!searchResultsModal || !searchResultsContainer || !searchLoading || !noResults || !closeModalBtn) {
    console.warn("Search functionality cannot initialize: Modal elements not found.");
    // return; // Optionally stop script execution if modal is essential
  }

  // --- Helper Functions ---
  function formatTrackDuration(seconds) {
    const numSeconds = Number(seconds); // Ensure it's a number
    if (isNaN(numSeconds) || numSeconds < 0) {
      return '0:00';
    }
    const minutes = Math.floor(numSeconds / 60);
    const remainingSeconds = Math.floor(numSeconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }


  function formatTotalDuration(totalSeconds) {
    const numSeconds = Number(totalSeconds); // Ensure it's a number
    if (isNaN(numSeconds) || numSeconds < 0) {
        return "0 min";
    }
    
    const hours = Math.floor(numSeconds / 3600);
    const minutes = Math.floor((numSeconds % 3600) / 60);
    const seconds = numSeconds % 60;

    let result = "";
    if (hours > 0) {
        result += `${hours} hr`;
        if (minutes > 0) {
            result += ` ${minutes} min`;
        }
    } else {
        if (minutes > 0) {
            result += `${minutes} min`;
            if (seconds > 0) {
                result += ` ${seconds} sec`;
            }
        } else {
            result = seconds > 0 ? `${seconds} sec` : "0 min";
        }
    }
    
    return result;
  }


  function parseDurationToSeconds(durationString) {
      if (!durationString || typeof durationString !== 'string') return 0;

      let totalSeconds = 0;
      const durationLower = durationString.toLowerCase().trim();
      
      // Handle "X hr Y min Z sec" format
      const hourMatch = durationLower.match(/(\d+)\s*hr/);
      if (hourMatch && hourMatch[1]) {
          totalSeconds += parseInt(hourMatch[1], 10) * 3600;
      }

      const minMatch = durationLower.match(/(\d+)\s*min/);
      if (minMatch && minMatch[1]) {
          totalSeconds += parseInt(minMatch[1], 10) * 60;
      }

      const secMatch = durationLower.match(/(\d+)\s*sec/);
      if (secMatch && secMatch[1]) {
          totalSeconds += parseInt(secMatch[1], 10);
      }
      
      // Handle MM:SS format (used for individual tracks)
      const timeMatch = durationLower.match(/^(\d+):(\d{2})$/);
      if (timeMatch && timeMatch[1] && timeMatch[2]) {
          totalSeconds = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
      }
      
      // If no matches found and it's just a number, assume it's already in seconds
      if (totalSeconds === 0 && /^\d+$/.test(durationLower)) {
          totalSeconds = parseInt(durationLower, 10);
      }
      
      return totalSeconds;
  }


  // --- Modal and Search Result Handling ---
  function displaySearchResults(results) {
    if (!searchResultsContainer || !noResults) return; // Check elements exist
    
    searchResultsContainer.innerHTML = ''; // Clear previous results
    noResults.style.display = results.length === 0 ? 'block' : 'none';
    
    results.forEach(track => {
      const resultItem = document.createElement('div');
      resultItem.className = 'search-result-item';
      // Store track data safely as JSON string
      resultItem.dataset.trackData = JSON.stringify(track); 
      
      const imageUrl = track.image_url || '/static/pictures/playlists/default_cover.jpg'; // Use placeholder if no image
      const trackDurationSec = typeof track.duration_sec === 'number' ? track.duration_sec : 0;

      resultItem.innerHTML = `
        <img src="${imageUrl}" alt="${track.name || 'Track'} cover" onerror="this.onerror=null; this.src='/static/pictures/playlists/default_cover.jpg';">
        <div class="search-result-info">
          <div class="search-result-title" title="${track.name || ''}">${track.name || 'Unknown Title'}</div>
          <div class="search-result-artist" title="${track.artists || ''}">${track.artists || 'Unknown Artist'}</div>
          <div class="search-result-album" title="${track.album || ''}">${track.album || 'Unknown Album'}</div>
        </div>
        <div class="search-result-duration">${formatTrackDuration(trackDurationSec)}</div>
        <button class="add-to-playlist-btn" data-track-id="${track.spotify_id || ''}" title="Add track to playlist">
          <i class="fas fa-plus"></i> Add
        </button>
      `;
      searchResultsContainer.appendChild(resultItem);
    });
  }
  
  /** Shows the search results modal */
  function showModal() {
    if (searchResultsModal) {
        searchResultsModal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scroll
    }
  }
  
  /** Hides the search results modal */
  function hideModal() {
    if (searchResultsModal) {
        searchResultsModal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restore background scroll
        // Clear stored playlist ID and any lingering results/state
        delete searchResultsModal.dataset.currentPlaylistId; 
        if (searchResultsContainer) searchResultsContainer.innerHTML = '';
        if (noResults) noResults.style.display = 'none';
    }
  }

  // --- Event Listeners ---

  // Search Form Submission (Handles multiple playlists)
  searchForms.forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault(); // Prevent default form submission

      if (!searchResultsModal || !searchLoading || !searchResultsContainer || !noResults) {
          console.error("Cannot perform search: Modal elements missing.");
          return;
      }

      const playlistId = this.dataset.playlistId; 
      const songTitleInput = this.querySelector('input[name="song_title"]');
      const artistNameInput = this.querySelector('input[name="artist_name"]');
      
      if (!playlistId || !songTitleInput || !artistNameInput) {
          console.error("Search form is missing necessary data attributes or input fields.");
          return;
      }
      const songTitle = songTitleInput.value.trim();
      const artistName = artistNameInput.value.trim();

      // Basic validation
      if (!songTitle && !artistName) {
          showNotification("Please enter at least a song title or artist name.", "warning");
          return;
      }

      searchLoading.style.display = 'flex'; // Use flex for centering spinner if needed
      searchResultsContainer.innerHTML = '';
      noResults.style.display = 'none';

      // Store the correct playlistId on the modal for later use
      searchResultsModal.dataset.currentPlaylistId = playlistId; 
      
      showModal(); // Show modal immediately, loading spinner is visible
      
      try {
        const queryParams = new URLSearchParams({
            title: songTitle,
            artist: artistName
            // Only include playlist_id if your backend uses it for context during search
            // playlist_id: playlistId 
        });
        const response = await fetch(`/search_song?${queryParams.toString()}`);
        
        if (!response.ok) {
            let errorMsg = `Search failed (${response.status})`;
            try { // Try to parse error details from backend if available
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch (parseError) { /* Ignore if response is not JSON */ }
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        displaySearchResults(data); // Display results (or 'no results' message if empty)

      } catch (error) {
        console.error('Error searching for songs:', error);
        if (searchResultsContainer) {
           searchResultsContainer.innerHTML = `<div class="no-results">Error: ${error.message}. Please try again.</div>`;
        } else {
            showNotification(`Search Error: ${error.message}`, 'danger');
        }
      } finally {
        if (searchLoading) searchLoading.style.display = 'none'; // Hide loading spinner
      }
    });
  });
  
  // Modal Closing Listeners (only if modal exists)
  if (closeModalBtn) {
      closeModalBtn.addEventListener('click', hideModal);
  }
  if (searchResultsModal) {
      searchResultsModal.addEventListener('click', (e) => { 
          // Close if click is on the overlay itself, not the content box
          if (e.target === searchResultsModal) hideModal(); 
      });
      document.addEventListener('keydown', (e) => { 
          // Close on Escape key
          if (e.key === 'Escape' && searchResultsModal.style.display === 'flex') hideModal(); 
      });
  }
  
  // Add Track Button Click (Handles multiple playlists and duration update)
  if (searchResultsContainer) {
      searchResultsContainer.addEventListener('click', async function(e) {
        const addButton = e.target.closest('.add-to-playlist-btn');
        if (addButton) {
          const resultItem = addButton.closest('.search-result-item');
          if (!resultItem || !resultItem.dataset.trackData) {
              console.error("Could not find track data for the clicked item.");
              return;
          }
          
          // Retrieve the correct playlistId stored on the modal
          const playlistId = searchResultsModal ? searchResultsModal.dataset.currentPlaylistId : null;

          if (!playlistId) {
             console.error("Add Track Error: Could not determine Playlist ID from modal data attribute.");
             showNotification('Error: Could not identify the target playlist. Please close modal and retry.', 'danger');
             return; 
          }
          
          // Find the corresponding playlist item in the main page DOM
          const playlistItemElement = document.querySelector(`.playlist-item[data-playlist-id="${playlistId}"]`); 
          if (!playlistItemElement) {
             console.warn(`Add Track Warning: Could not find playlist item element with ID ${playlistId} in the DOM to update view after adding.`);
             // Proceed with adding, but view won't update automatically
          }

          let trackData;
          try {
             trackData = JSON.parse(resultItem.dataset.trackData);
          } catch (jsonError) {
             console.error("Add Track Error: Failed to parse track data.", jsonError);
             showNotification('Error: Could not read track data.', 'danger');
             return;
          }

          // Ensure duration is a number, default to 0 if missing/invalid
          const trackDurationSeconds = typeof trackData.duration_sec === 'number' ? trackData.duration_sec : 0; 

          const addTrackUrl = `/playlist/${playlistId}/add_track`; 
          
          // Provide visual feedback and prevent double clicks
          addButton.disabled = true; 
          const originalButtonContent = addButton.innerHTML;
          addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

          try {
            const response = await fetch(addTrackUrl, {
              method: 'POST',
              headers: { 
                  'Content-Type': 'application/json',
                  // Include CSRF token header if needed by your backend framework
                  // 'X-CSRFToken': getCsrfToken() // Example function to get token
              },
              // Send the full track data object as retrieved from search
              body: JSON.stringify({ track: trackData }) 
            });
            
            const responseData = await response.json(); // Expect { message, track: { id, title, artist, album, duration } } on success
            
            if (response.ok && responseData.success) {
              showNotification(responseData.message, 'success');
              
              if (responseData.track) {
                const addedDurationConfirmed = typeof responseData.track.duration === 'number' 
                                                ? responseData.track.duration 
                                                : trackDurationSeconds;
                updatePlaylistView(playlistItemElement, responseData.track, playlistId, addedDurationConfirmed);
              }
              
              // Clear the search form fields
              const searchForm = document.querySelector(`.song-search-form[data-playlist-id="${playlistId}"]`);
              if (searchForm) {
                  const songTitleInput = searchForm.querySelector('input[name="song_title"]');
                  const artistNameInput = searchForm.querySelector('input[name="artist_name"]');
                  if (songTitleInput) songTitleInput.value = '';
                  if (artistNameInput) artistNameInput.value = '';
              }
              
              hideModal();

            } else {
              throw new Error(responseData.error || `Failed to add track (${response.status})`);
            }
          } catch (error) {
            console.error('Error adding track to playlist:', error);
            showNotification(`Error: ${error.message}`, 'danger');
            // Re-enable button on error
            addButton.disabled = false; 
            addButton.innerHTML = originalButtonContent;
          }
        }
      });
  }

  // --- DOM Update Functions ---
  function updatePlaylistView(playlistItemElement, addedTrackServerData, playlistId, addedDurationSec) {
      const playlistContent = playlistItemElement.querySelector('.playlist-content');
      if (!playlistContent) {
          console.error("Cannot update playlist view: .playlist-content not found inside playlist item.");
          return;
      }
      
      // Remove "No tracks" message if present
      const noTracksMessage = playlistContent.querySelector('.no-tracks');
      if (noTracksMessage) noTracksMessage.remove();
      
      let trackListElement = playlistContent.querySelector('ol.track-list');
      
      // Create track list header and list container if they don't exist
      if (!trackListElement) {
          const headerExists = playlistContent.querySelector('.track-list-header');
          if (!headerExists) {
              const trackListHeader = document.createElement('div');
              trackListHeader.className = 'track-list-header';
              // Match structure from account.html
              trackListHeader.innerHTML = `
                <span class="header-number">#</span>
                <span class="header-title">Title</span>
                <span class="header-album">Album</span>
                <span class="header-duration"><i class="far fa-clock"></i></span>
                <span class="header-delete">&nbsp;</span> 
              `;
              // Prepend header before where the list will go
              playlistContent.insertBefore(trackListHeader, playlistContent.querySelector('.search-song-form')); 
          }

          trackListElement = document.createElement('ol');
          trackListElement.className = 'track-list';
          // Insert the new list after the header (or at the start if header existed but list didn't)
          const referenceNode = playlistContent.querySelector('.track-list-header') 
                               ? playlistContent.querySelector('.track-list-header').nextSibling 
                               : playlistContent.firstChild; // Fallback insert position
          playlistContent.insertBefore(trackListElement, referenceNode);
      }
      
      // Add the new track item to the list
      const trackCount = trackListElement.children.length;
      const newTrackItem = document.createElement('li');
      newTrackItem.className = 'track-item';
      // Use the definitive track ID returned by the server after adding
      newTrackItem.dataset.trackId = addedTrackServerData.id; 

      // Construct innerHTML matching account.html structure
      newTrackItem.innerHTML = `
        <span class="track-number">${trackCount + 1}</span>
        <div class="track-details">
          <span class="track-title">${addedTrackServerData.title || 'Unknown Title'}</span>
          <span class="track-artist">${addedTrackServerData.artist || 'Unknown Artist'}</span>
        </div>
        <span class="track-album">${addedTrackServerData.album || 'Unknown'}</span>
        <span class="track-duration">${formatTrackDuration(addedDurationSec)}</span>
        <form action="/playlist/${playlistId}/remove_track" method="POST" class="delete-track-form">
          <input type="hidden" name="playlist_track_id" value="${addedTrackServerData.id}">
          <button type="submit" class="btn btn-danger btn-sm" title="Delete track">
            <i class="fas fa-trash-alt"></i>
          </button>
        </form>
      `;
      trackListElement.appendChild(newTrackItem);
      
      // --- Update Summary Information (Song Count and Duration) ---
      const playlistHeader = playlistItemElement.querySelector('.playlist-header');
      if (!playlistHeader) {
          console.warn("Could not find .playlist-header to update count/duration.");
          return; // Stop if header isn't found
      }

      // Update song count in the header
      const songCountElement = playlistHeader.querySelector('.playlist-song-count');
      if (songCountElement) {
        // Read current count more robustly
        const countMatch = songCountElement.textContent.match(/(\d+)/);
        const currentCount = countMatch ? parseInt(countMatch[0], 10) : 0;
        songCountElement.textContent = `${currentCount + 1} song${currentCount === 0 ? '' : 's'}`; 
      } else {
           console.warn("Could not find .playlist-song-count element.");
      }

      // Update Total Duration in the header
      const totalDurationElement = playlistHeader.querySelector('.playlist-duration');
      if (totalDurationElement) {
          const currentDurationString = totalDurationElement.textContent.trim();
          let currentTotalSeconds = 0;
          
          try {
              currentTotalSeconds = parseDurationToSeconds(currentDurationString);
              if (isNaN(currentTotalSeconds)) {
                  console.warn("Invalid current duration format:", currentDurationString);
                  currentTotalSeconds = 0;
              }
          } catch (error) {
              console.error("Error parsing current duration:", error);
              currentTotalSeconds = 0;
          }

          // Validate the new track's duration
          const newTrackDuration = typeof addedDurationSec === 'number' && !isNaN(addedDurationSec) 
              ? Math.max(0, addedDurationSec) 
              : 0;

          const newTotalSeconds = currentTotalSeconds + newTrackDuration;
          totalDurationElement.textContent = formatTotalDuration(newTotalSeconds);
      } else {
          console.warn("Could not find .playlist-duration element in header to update.");
      }
  }


  function showNotification(message, type) {
    const container = document.querySelector('.flash-messages');
    if (!container) {
        console.error("'.flash-messages' container not found for notification!");
        // Fallback to browser alert if container is missing
        alert(`${type.toUpperCase()}: ${message}`); 
        return;
    }

    const notification = document.createElement('div');
    // Match classes used in account.html for server-rendered messages if possible
    notification.className = `alert alert-${type} fade custom-alert`; 
    notification.setAttribute('role', 'alert');
    notification.innerHTML = message; // Remove the close button HTML
    
    container.appendChild(notification);
    
    // Make it visible (Bootstrap 'fade' needs 'show' added)
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
         if (notification.parentNode) { // Check if user hasn't manually closed it
            notification.classList.remove('show');
            // Use transitionend event for smoother removal if possible, else fallback timeout
            notification.addEventListener('transitionend', () => {
                if (notification.parentNode) notification.remove();
            }, { once: true }); // Remove listener after firing once

            // Fallback removal if transitionend doesn't fire (e.g., no transition defined)
            setTimeout(() => {
                 if (notification.parentNode) notification.remove();
            }, 350); // Slightly longer than typical transition
        }
    }, 3000);
  }

});
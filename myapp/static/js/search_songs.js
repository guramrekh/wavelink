document.addEventListener('DOMContentLoaded', function() {
  // Auto-dismiss for existing server-rendered flash messages
  const existingFlashMessages = document.querySelectorAll('.flash-messages .custom-alert');
  existingFlashMessages.forEach(notification => {
    if (notification.classList.contains('show') && !notification.dataset.hiding) {
        notification.dataset.hiding = 'true';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                notification.classList.add('hide');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300); 
            }
        }, 3000);
    } else if (!notification.classList.contains('hide') && !notification.dataset.hiding) {
        notification.offsetHeight; 
        notification.classList.add('show');
        notification.dataset.hiding = 'true';
        setTimeout(() => {
             if (notification.parentNode) {
                notification.classList.remove('show');
                notification.classList.add('hide');
                setTimeout(() => {
                   if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 3000);
    }
  });

  const searchForms = document.querySelectorAll('.song-search-form');
  const searchResultsModal = document.getElementById('search-results-modal');
  const searchResultsContainer = document.getElementById('search-results-container');
  const searchLoading = document.getElementById('search-loading');
  const noResults = document.getElementById('no-results');
  const closeModalBtn = searchResultsModal ? searchResultsModal.querySelector('.close-modal') : null;

  if (!searchResultsModal || !searchResultsContainer || !searchLoading || !noResults || !closeModalBtn) {
    console.warn("Search functionality cannot initialize: Modal elements not found.");
  }

  // Helper Functions 
  function formatTrackDuration(seconds) {
    const numSeconds = Number(seconds);
    if (isNaN(numSeconds) || numSeconds < 0) {
      return '0:00';
    }
    const minutes = Math.floor(numSeconds / 60);
    const remainingSeconds = Math.floor(numSeconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  function formatTotalDuration(totalSeconds) {
    const numSeconds = Number(totalSeconds);
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
      
      const timeMatch = durationLower.match(/^(\d+):(\d{2})$/);
      if (timeMatch && timeMatch[1] && timeMatch[2]) {
          totalSeconds = parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
      }
      
      if (totalSeconds === 0 && /^\d+$/.test(durationLower)) {
          totalSeconds = parseInt(durationLower, 10);
      }
      
      return totalSeconds;
  }


  // Modal and Search Result Handling 
  function displaySearchResults(results) {
    if (!searchResultsContainer || !noResults) return;
    
    searchResultsContainer.innerHTML = '';
    noResults.style.display = results.length === 0 ? 'block' : 'none';
    
    results.forEach(track => {
      const resultItem = document.createElement('div');
      resultItem.className = 'search-result-item';
      resultItem.dataset.trackData = JSON.stringify(track); 
      
      const imageUrl = track.image_url || '/static/pictures/playlists/default_cover.jpg';
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
  
  function showModal() {
    if (searchResultsModal) {
        searchResultsModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
  }
  
  function hideModal() {
    if (searchResultsModal) {
        searchResultsModal.style.display = 'none';
        document.body.style.overflow = 'auto';
        delete searchResultsModal.dataset.currentPlaylistId; 
        if (searchResultsContainer) searchResultsContainer.innerHTML = '';
        if (noResults) noResults.style.display = 'none';
    }
  }

  // Event Listeners 
  // Search Form Submission (Handles multiple playlists)
  searchForms.forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();

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

      if (!songTitle && !artistName) {
          showNotification("Please enter at least a song title or artist name.", "warning");
          return;
      }

      searchLoading.style.display = 'flex';
      searchResultsContainer.innerHTML = '';
      noResults.style.display = 'none';

      searchResultsModal.dataset.currentPlaylistId = playlistId; 
      
      showModal();
      
      try {
        const queryParams = new URLSearchParams({
            title: songTitle,
            artist: artistName
        });
        const response = await fetch(`/search_song?${queryParams.toString()}`);
        
        if (!response.ok) {
            let errorMsg = `Search failed (${response.status})`;
            try {
                const errorData = await response.json();
                errorMsg = errorData.error || errorMsg;
            } catch (parseError) {}
            throw new Error(errorMsg);
        }
        
        const data = await response.json();
        displaySearchResults(data);

      } catch (error) {
        console.error('Error searching for songs:', error);
        if (searchResultsContainer) {
           searchResultsContainer.innerHTML = `<div class="no-results">Error: ${error.message}. Please try again.</div>`;
        } else {
            showNotification(`Search Error: ${error.message}`, 'danger');
        }
      } finally {
        if (searchLoading) searchLoading.style.display = 'none';
      }
    });
  });
  
  // Modal Closing Listeners (only if modal exists)
  if (closeModalBtn) {
      closeModalBtn.addEventListener('click', hideModal);
  }
  if (searchResultsModal) {
      searchResultsModal.addEventListener('click', (e) => { 
          if (e.target === searchResultsModal) hideModal(); 
      });
      document.addEventListener('keydown', (e) => { 
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
          
          const playlistId = searchResultsModal ? searchResultsModal.dataset.currentPlaylistId : null;

          if (!playlistId) {
             console.error("Add Track Error: Could not determine Playlist ID from modal data attribute.");
             showNotification('Error: Could not identify the target playlist. Please close modal and retry.', 'danger');
             return; 
          }
          
          const playlistItemElement = document.querySelector(`.playlist-item[data-playlist-id="${playlistId}"]`); 
          if (!playlistItemElement) {
             console.warn(`Add Track Warning: Could not find playlist item element with ID ${playlistId} in the DOM to update view after adding.`);
          }

          let trackData;
          try {
             trackData = JSON.parse(resultItem.dataset.trackData);
          } catch (jsonError) {
             console.error("Add Track Error: Failed to parse track data.", jsonError);
             showNotification('Error: Could not read track data.', 'danger');
             return;
          }

          const trackDurationSeconds = typeof trackData.duration_sec === 'number' ? trackData.duration_sec : 0; 

          const addTrackUrl = `/playlist/${playlistId}/add_track`; 
          
          addButton.disabled = true; 
          const originalButtonContent = addButton.innerHTML;
          addButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';

          try {
            const response = await fetch(addTrackUrl, {
              method: 'POST',
              headers: { 
                  'Content-Type': 'application/json',
                  // Potential CSRF token
              },
              body: JSON.stringify({ track: trackData }) 
            });
            
            const responseData = await response.json();
            
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
            addButton.disabled = false; 
            addButton.innerHTML = originalButtonContent;
          }
        }
      });
  }

  // DOM Update Functions 
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
              trackListHeader.innerHTML = `
                <span class="header-number">#</span>
                <span class="header-title">Title</span>
                <span class="header-album">Album</span>
                <span class="header-duration"><i class="far fa-clock"></i></span>
                <span class="header-delete">&nbsp;</span> 
              `;
              playlistContent.insertBefore(trackListHeader, playlistContent.querySelector('.search-song-form')); 
          }

          trackListElement = document.createElement('ol');
          trackListElement.className = 'track-list';
          const referenceNode = playlistContent.querySelector('.track-list-header') 
                               ? playlistContent.querySelector('.track-list-header').nextSibling 
                               : playlistContent.firstChild; // Fallback insert position
          playlistContent.insertBefore(trackListElement, referenceNode);
      }
      
      // Add the new track item to the list
      const trackCount = trackListElement.children.length;
      const newTrackItem = document.createElement('li');
      newTrackItem.className = 'track-item';
      newTrackItem.dataset.trackId = addedTrackServerData.id; 

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
      
      // Update Summary Information (Song Count and Duration) 
      const playlistHeader = playlistItemElement.querySelector('.playlist-header');
      if (!playlistHeader) {
          console.warn("Could not find .playlist-header to update count/duration.");
          return;
      }

      // Update song count in the header
      const songCountElement = playlistHeader.querySelector('.playlist-song-count');
      if (songCountElement) {
        const countMatch = songCountElement.textContent.match(/(\d+)/);
        const currentCount = countMatch ? parseInt(countMatch[0], 10) : 0;
        songCountElement.textContent = `${currentCount + 1} song${currentCount === 0 ? '' : 's'}`; 
      } else {
           console.warn("Could not find .playlist-song-count element.");
      }

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
        alert(`${type.toUpperCase()}: ${message}`); 
        return;
    }

    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fade custom-alert`; 
    notification.setAttribute('role', 'alert');
    notification.innerHTML = message; 
    
    container.appendChild(notification);
    
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    setTimeout(() => {
         if (notification.parentNode) { 
            notification.classList.remove('show');
            notification.addEventListener('transitionend', () => {
                if (notification.parentNode) notification.remove();
            }, { once: true });

            setTimeout(() => {
                 if (notification.parentNode) notification.remove();
            }, 350);
        }
    }, 3000);
  }

});
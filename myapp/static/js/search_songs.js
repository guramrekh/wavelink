document.addEventListener('DOMContentLoaded', function() {
  // Get all search forms
  const searchForms = document.querySelectorAll('.song-search-form');
  const searchResultsModal = document.getElementById('search-results-modal');
  const searchResultsContainer = document.getElementById('search-results-container');
  const searchLoading = document.getElementById('search-loading');
  const noResults = document.getElementById('no-results');
  const closeModalBtn = searchResultsModal.querySelector('.close-modal');
  
  // Function to format duration (convert seconds to MM:SS format)
  function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) {
      return '0:00';
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  
  // Function to display search results
  function displaySearchResults(results) {
    searchResultsContainer.innerHTML = '';
    
    if (results.length === 0) {
      noResults.style.display = 'block';
      return;
    }
    
    noResults.style.display = 'none';
    
    results.forEach(track => {
      const resultItem = document.createElement('div');
      resultItem.className = 'search-result-item';
      
      // Store the original track data as a data attribute
      resultItem.dataset.trackData = JSON.stringify(track);
      
      // Handle image URL - use the image_url property
      const imageUrl = track.image_url || '/static/pictures/playlists/default_cover.jpg';
      
      resultItem.innerHTML = `
        <img src="${imageUrl}" alt="${track.name} album cover" onerror="this.src='/static/pictures/playlists/default_cover.jpg'">
        <div class="search-result-info">
          <div class="search-result-title">${track.name}</div>
          <div class="search-result-artist">${track.artists}</div>
          <div class="search-result-album">${track.album || 'Unknown Album'}</div>
        </div>
        <div class="search-result-duration">${formatDuration(track.duration_sec)}</div>
        <button class="add-to-playlist-btn" data-track-id="${track.spotify_id}">
          <i class="fas fa-plus"></i> Add
        </button>
      `;
      
      searchResultsContainer.appendChild(resultItem);
    });
  }
  
  // Function to show the modal
  function showModal() {
    searchResultsModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
  
  // Function to hide the modal
  function hideModal() {
    searchResultsModal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
  
  // Add event listeners to all search forms
  searchForms.forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const playlistId = this.dataset.playlistId;
      const songTitle = this.querySelector('input[name="song_title"]').value;
      const artistName = this.querySelector('input[name="artist_name"]').value;
      
      // Show loading state
      searchLoading.style.display = 'block';
      searchResultsContainer.innerHTML = '';
      noResults.style.display = 'none';
      
      // Show the modal
      showModal();
      
      try {
        // Make API request to search_song endpoint
        const response = await fetch(`/search_song?playlist_id=${playlistId}&title=${encodeURIComponent(songTitle)}&artist=${encodeURIComponent(artistName)}`);
        
        if (!response.ok) {
          throw new Error('Search failed');
        }
        
        const data = await response.json();
        
        // Display the results
        displaySearchResults(data);
      } catch (error) {
        console.error('Error searching for songs:', error);
        searchResultsContainer.innerHTML = '<div class="no-results">An error occurred while searching. Please try again.</div>';
      } finally {
        // Hide loading state
        searchLoading.style.display = 'none';
      }
    });
  });
  
  // Close modal when clicking the close button
  closeModalBtn.addEventListener('click', hideModal);
  
  // Close modal when clicking outside the modal content
  searchResultsModal.addEventListener('click', function(e) {
    if (e.target === searchResultsModal) {
      hideModal();
    }
  });
  
  // Close modal when pressing Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && searchResultsModal.style.display === 'flex') {
      hideModal();
    }
  });
  
  // Handle adding tracks to playlist
  searchResultsContainer.addEventListener('click', async function(e) {
    if (e.target.closest('.add-to-playlist-btn')) {
      const button = e.target.closest('.add-to-playlist-btn');
      const resultItem = button.closest('.search-result-item');
      const playlistId = document.querySelector('.song-search-form').dataset.playlistId;
      
      // Get the original track data
      const track = JSON.parse(resultItem.dataset.trackData);
      const url = `/playlist/${playlistId}/add_track`;
      
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            track: track
          })
        });
        
        const data = await response.json();
        
        if (response.ok) {
          // Show success message
          alert(data.message || 'Track added successfully!');
          // Optionally close the modal
          hideModal();
        } else {
          // Show error message
          alert(data.error || 'Failed to add track to playlist');
        }
      } catch (error) {
        console.error('Error adding track to playlist:', error);
        alert('An error occurred while adding the track to the playlist');
      }
    }
  });
}); 
document.addEventListener('DOMContentLoaded', function() {
  const toggleButtons = document.querySelectorAll('.toggle-comments-btn');
  toggleButtons.forEach(button => {
    button.addEventListener('click', function() {
      const playlistId = this.dataset.playlistId;
      const commentsSection = document.getElementById(`comments-${playlistId}`);
      const commentCountSpan = this.querySelector(`span.comment-count-${playlistId}`);
      const currentCount = commentCountSpan ? commentCountSpan.textContent : '';

      if (commentsSection.style.display === 'none' || commentsSection.style.display === '') {
        commentsSection.style.display = 'block';
      } else {
        commentsSection.style.display = 'none';
      }
    });
  });
}); 
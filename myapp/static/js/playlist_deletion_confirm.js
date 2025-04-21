
let formIdToDelete = null;
  
document.querySelectorAll('.delete-item').forEach(button => {
  button.addEventListener('click', () => {
    formIdToDelete = button.getAttribute('data-form-id');
    document.getElementById('confirm-modal').style.display = 'flex';
  });
});

document.getElementById('cancel-delete').addEventListener('click', () => {
  formIdToDelete = null;
  document.getElementById('confirm-modal').style.display = 'none';
});

document.getElementById('confirm-delete').addEventListener('click', () => {
  if (formIdToDelete) {
    document.getElementById(formIdToDelete).submit();
  }
});
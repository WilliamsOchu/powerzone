let phone__number = document.querySelector('input[type="tel"]').value
let form = document.getElementById('form')



form.addEventListener('submit', (e) => {
    trimmed__number = parseInt(phone__number.slice(1))
})
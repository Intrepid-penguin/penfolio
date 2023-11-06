const cform = document.querySelector('.cform')
const covert = document.querySelector('.covert')
const close = document.querySelector('.close')

covert.addEventListener('click', () => {
    cform.setAttribute('open', true)
})

close.addEventListener('click', () => {
    cform.setAttribute('open', 'false')
})
const cform = document.querySelector('.cform')
const covert = document.querySelector('.covert')
const close = document.querySelector('.close')


window.addEventListener('load', (event) => {
    console.log(cform.getAttribute('display'))
    cform.getAttribute('display') === 'true' ? cform.setAttribute('open', true) : null
})

covert.addEventListener('click', () => {
    cform.setAttribute('open', true)
})

close.addEventListener('click', () => {
    cform.setAttribute('open', 'false')
    cform.getAttribute('display', 'false')
    let url = new URLSearchParams(location.search)
    url.delete('display')
    window.history.replaceState({}, '', `${window.location.pathname}`)
})
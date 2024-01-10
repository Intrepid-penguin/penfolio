
const deleteBtn = document.querySelector('.delete_btn')
const confirmModal = document.querySelector('.confirm_modal')
const cancelBtn = document.querySelector('.cancel_btn')

deleteBtn.addEventListener('click', () => {
    let isOpen = confirmModal.getAttribute('data-opened')
    console.log(isOpen)
    isOpen === 'false' ? confirmModal.setAttribute('data-opened', 'true') : null
})

cancelBtn.addEventListener('click', () => {
    let isOpen = confirmModal.getAttribute('data-opened')
    console.log(isOpen)
    isOpen === 'true' ? confirmModal.setAttribute('data-opened', 'false') : null
})


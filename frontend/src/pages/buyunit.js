let open__popup = document.getElementById('open__modal')
let close__popup = document.getElementById('close__icon')
let modal = document.getElementById('modal')
let meter__form = document.getElementById('meter__form')
let disco = document.getElementById('disco__field')
let meter__number = document.getElementById('meter__field')



let unit__method = document.getElementById('unit__method__select')
let __qty__ = document.getElementById('qty__val')
let unit__method__form = document.getElementById('unit__method__form')



let error__message = document.getElementById('error__message')
let unit__error__message = document.getElementById('unit_error__message')

let __err__ = "Select a valid Disco"
let __err__unit__method = 'Select a method of purchase'



let __band__ = document.getElementById('band__select__menu')



disco.addEventListener('input', () => {
    meter__form.addEventListener('submit', (e) => {
        e.preventDefault()
        
        if (disco.selectedIndex === 0) {
            error__message.style.display = 'block'
            error__message.textContent = __err__
            disco.addEventListener('input', ()=>{
                if (disco.selectedIndex !== 0) {
                    error__message.style.display = 'none'
                }
            })
        } else {
            modal.classList.add('open')
        }

        close__popup.addEventListener('click', ()=>{
            modal.classList.remove('open')
        })

    })
})




// Unit method selection

__qty__.disabled = true
unit__method.addEventListener('input', ()=>{
    if (unit__method.selectedIndex === 0 || unit__method.value === 'choose__method') {
        __qty__.disabled = true
        __qty__.placeholder = 'Select a method'
    } else if (unit__method.selectedIndex === 1) {
        __qty__.disabled = false
        __qty__.placeholder = 'How many Units do you want to Purchase'
    } else if (unit__method.selectedIndex === 2) {
        __qty__.disabled = false
        __qty__.placeholder = 'Enter a Price and get Unit equivalent'
    }

    unit__method__form.addEventListener('submit', (e)=>{
        e.preventDefault()
    })


})
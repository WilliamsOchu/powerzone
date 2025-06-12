let menu__list = document.querySelector('.nav__links')
let toggle__icon = document.querySelector('.fa-bars')

menu__list.style.maxHeight = "0px"



function toggle__menu() {
    if (menu__list.style.maxHeight == '0px') {
        menu__list.style.maxHeight = '50vh'
    } else {
        menu__list.style.maxHeight = '0px'
    }
}
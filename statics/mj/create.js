const Day = document.querySelector(".day")

const Hours = document.querySelector(".hr")

const Min = document.querySelector(".min")



function time() {
    let d = new Date()

    let hr = d.getHours()

    let min = d.getMinutes()

    const weekday = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    let day = weekday[d.getDay()]

    let x 
    if (hr >= 12) {
        x = " pm"
    }else {
        x = " am"
    }  
  
    if (min < 10) {
        nmin = `0${min}`
    }else{
        nmin = min
    }

Day.innerHTML= day
Hours.innerHTML = hr
Min.innerHTML = nmin + x
setTimeout(time, 1000);
}

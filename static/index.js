const url_regex = new RegExp(/(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)/)

function validateUrl(target) {
    if (target.value) {
        let validation = url_regex.test(target.value)

        if (!validation) {
            target.classList.add('is-danger')
        } else {
            target.classList.remove('is-danger')
        }
        return validation
    }
}

function loadUrls() {
    let tableElement = document.getElementById('tbody')
    let loadMoreElement = document.getElementById('load-more')

    fetch(loadMoreElement.getAttribute('data')).then((response) => response.json().then((data) => {
        if (data.next_page) {
            loadMoreElement.setAttribute('data', data.next_page)
        } else {
            loadMoreElement.disabled = true
        }
        data.data.forEach(element => {
            let urlElem = document.createElement('tr')
            urlElem.innerHTML = `<td><p class="is-underlined">${element.subpart}</p></td><td>${element.url}</td>`
            tableElement.appendChild(urlElem)
        });
    }))
}

function main() {
    let urlElement = document.getElementById('url')
    validateUrl(urlElement)
    urlElement.addEventListener('input', function (e) {
        validateUrl(e.target)
    })

    document.getElementById('shorter-form').addEventListener('submit', function (e) {
        e.preventDefault()

        let errorsElement = document.getElementById('errors')
        let urlInput = document.getElementById('url')
        if (!validateUrl(urlInput)) {
            errorsElement.innerHTML = `<div class="notification is-danger">Url incorrect</div>`
            return
        }
        let subpartInput = document.getElementById('subpart')

        let data = { url: urlInput.value, subpart: subpartInput.value }

        fetch('/s/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json;charset=utf-8'
            },
            body: JSON.stringify(data)
        }).then((response) => response.json().then((result) => {

            if (response.status == 403) {
                if (result.invalid == 'subpart') {
                    subpartInput.classList.add('is-danger')
                };
                errorsElement.innerHTML = `<div class="notification is-danger">${result.message}</div>`
            } else {
                subpartInput.classList.remove('is-danger')
                errorsElement.innerHTML = ''
                let tableElement = document.getElementById('tbody')
                let urlElem = document.createElement('tr')

                urlElem.innerHTML = `<td><p class="is-underlined">${result.subpart}</p></td><td>${result.url}</td>`
                tableElement.insertBefore(urlElem, tableElement.firstChild)
            }
        }))

    })

    let loadMoreElement = document.getElementById('load-more')
    loadMoreElement.addEventListener('click', function (e) {
        loadUrls()
    })
    loadUrls()

    document.querySelector('body').addEventListener('click', function (e) {
        if (e.target.tagName.toLowerCase() === 'p' && e.target.classList.contains('is-underlined')) {
            navigator.clipboard.writeText(`${window.location.host}/s/${e.target.innerText}/`)
            alert("Copied to clipboard")
        }
    })
}

main()

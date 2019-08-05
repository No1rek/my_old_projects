document.addEventListener("DOMContentLoaded", function() {
    var aside = document.querySelector('.main__aside'),
        recent = document.querySelector('.js-articles__recent'),
        mostViewed = document.querySelector('.js-articles__most-viewed'),
        mostLiked = document.querySelector('.js-articles__most-liked'),
        recentItem = aside.querySelector('.js-aside__recent'),
        mostViewedItem = aside.querySelector('.js-aside__most-viewed'),
        mostLikedItem = aside.querySelector('.js-aside__most-liked'),
        asideItems = aside.querySelectorAll('.aside__item'),
        offset = aside.offsetTop;

    window.onscroll = function() {
        var scrolled = (window.pageYOffset || document.documentElement.scrollTop) + 150;

        if (scrolled > offset) {
            aside.classList.add('aside_fixed');
            console.log(scrolled + ' ' + offset)
        } else {
            aside.classList.remove('aside_fixed');
        }

        if (scrolled > recent.offsetTop && scrolled < mostViewed.offsetTop && scrolled < mostLiked.offsetTop) {
            clearAll();
            recentItem.className += ' aside__item_active';
        }
        if (scrolled > mostViewed.offsetTop && scrolled < mostLiked.offsetTop) {
            clearAll();
            mostViewedItem.className += ' aside__item_active';
        }
        if (scrolled > mostLiked.offsetTop) {
            clearAll();
            mostLikedItem.className += ' aside__item_active';
        }
    };

    function clearAll () {
        asideItems.forEach(function (p1, p2, p3) {
            p1.className = p1.className.replace(' aside__item_active', '');
        })
    }


    asideItems.forEach(function (p1, p2, p3) {
        p1.addEventListener('click', function () {
            event.preventDefault();

            //забираем идентификатор бока с атрибута href
            var id  = $(this).attr('href'),

                //узнаем высоту от начала страницы до блока на который ссылается якорь
                top = $(id).offset().top - 40;

            //анимируем переход на расстояние - top за 1000 мс
            $('body,html').animate({scrollTop: top}, 1000);
        })
    });
});
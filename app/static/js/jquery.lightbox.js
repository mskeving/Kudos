$(document).ready(function(){

	// Open Lightbox
	$('.js--lightbox').live('click', function(e){

		e.preventDefault();

		var img = $(this).attr('href');

		$('body').append('<div class="lightbox cn-c"><i title="Close" class="fa fa-times lightbox__close"></i><div class="lightbox__img cn-w"><img src="' + img + '" /></div></div>');

		initLightbox();

	});

	// Close Lightbox
	function closeLightbox() {
		$('.lightbox').remove();
		$('html').removeClass('js--lightbox-open');
	};

	// Esc triggers closeLightbox
	document.onkeydown = function(evt) {
		evt = evt || window.event;
		if (evt.keyCode == 27) {
			closeLightbox();
		}
	};

	// Clicking triggers closeLightbox
	function initLightbox() {
		$('html').addClass('js--lightbox-open');

		$('*').one('click', function(){
			closeLightbox();
		});
	};

});

$(window).scroll(function() {
	var scrollInAction = false;

	return function() {
		var post_column_height = $('.post-column').height();
		var post_column_offset_top = $('.post-column').offset().top;

		if($(window).scrollTop() + $(window).height() >= post_column_offset_top + post_column_height ){
			
			if (scrollInAction) return false;
			scrollInAction = true;
			// pass in last post_id on page to specify where next group of posts should start
			last_post_on_page = $('.post').last();
			last_post_id = last_post_on_page.data('post-id');
			data = {
				last_post_id: last_post_id
			}
			$.ajax({
				url: '/get_more_posts',
				type: 'POST',
				data: data,
				success: function(new_posts){
					$('.post-column').append(new_posts);
					scrollInAction = false;

				},
				error: function(){
					console.log('failed to load more posts');
					scrollInAction = false;
				},
				dataType: 'json'
			})
		}
	}
}());
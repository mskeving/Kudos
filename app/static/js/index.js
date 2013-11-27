$(document).ready(function(){

	$(window).scroll(function() {
		var scrollInAction = false;

		return function() {

			if($('.post-column').length > 0) {
				//only index, user, and team pages will have .post-column
				if ($('.loaded').length > 0){
					//if all posts are loaded, don't try to fetch more until page refresh
					return
				}
				var post_column_height = $('.post-column').height();
				var post_column_offset_top = $('.post-column').offset().top;

				if($(window).scrollTop() + $(window).height() >= post_column_offset_top + post_column_height ){

					if (scrollInAction) return false;
					scrollInAction = true;
					$('.post-column.posts__home').append('<p class="js--loading-posts promo loading faded"><i class="fa fa-heart"></i>  Loading more posts</p>');
					// pass in last post_id on page to specify where next group of posts should start
					last_post_on_page = $('.posts__home .post').last();
					last_post_id = last_post_on_page.data('post-id');
					data = {
						last_post_id: last_post_id
					}
					$.ajax({
						url: '/get_more_posts',
						type: 'POST',
						data: data,
						success: function(new_posts){
							$('.loading').remove()
							if (new_posts && initCommentButtons($(new_posts))){
								$('.post-column.posts__home').append(new_posts);
							}
							else if (!$('.loaded').length>0) {
								$('.post-column.posts__home').append('<p class="promo loaded faded">Made with <i class="fa fa-heart"></i> by <a href="/team/Kudos">Team Kudos</a>.</p>');
							}
							initCommentButtons($('.post[data-post-id]'));
							initRemoveButton($('.post[data-post-id] .remove-post-button'));
							scrollInAction = false;
						},
						error: function(){

							$('.post-column.posts__home').append('<p class="promo error-loading faded"><i class="fa fa-times"></i>  Error loading posts</p>');
							scrollInAction = false;
						},
						dataType: 'json'
					})
				}
			}
		}
	}());
});
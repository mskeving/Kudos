// Detect support for CSS animations
function CSSAnimation(){
	/*
	    webkitAnimationName => Safari/Chrome
	    MozAnimationName => Mozilla Firefox
	    OAnimationName => Opera
	    animationName => compliant browsers (inc. IE10)
	 */
	var supported = false;
	var prefixes = ['webkit', 'Moz', 'O', ''];
	var limit = prefixes.length;
	var doc = document.documentElement.style;
	var prefix, start, end;

	while (limit--) {
	    // If the compliant browser check (in this case an empty string value) then we need to check against different string (animationName and not prefix + AnimationName)
	    if (!prefixes[limit]) {
	        // If not undefined then we've found a successful match
	        if (doc['animationName'] !== undefined) {
	            prefix = prefixes[limit];
	            start = 'animationstart';
	            end = 'animationend';
	            supported = true;
	            break;
	        }
	    }
	    // Other brower prefixes to be checked
	    else {
	        // If not undefined then we've found a successful match
	        if (doc[prefixes[limit] + 'AnimationName'] !== undefined) {
	            prefix = prefixes[limit];

	            switch (limit) {
	                case 0:
	                    //  webkitAnimationStart && webkitAnimationEnd
	                    start = prefix.toLowerCase() + 'AnimationStart';
	                    end = prefix.toLowerCase() + 'AnimationEnd';
	                    supported = true;
	                    break;

	                case 1:
	                    // animationstart && animationend
	                    start = 'animationstart';
	                    end = 'animationend';
	                    supported = true;
	                    break;

	                case 2:
	                    // oanimationstart && oanimationend
	                    start = prefix.toLowerCase() + 'animationstart';
	                    end = prefix.toLowerCase() + 'animationend';
	                    supported = true;
	                    break;
	            }

	            break;
	        }
	    }
	}

	return {
	    supported: supported,
	    prefix: prefix,
	    start: start,
	    end: end
	};
}

// Set up check for animation support
var animations = CSSAnimation();

// Prepare modal closing links/buttons
function prepModals() {
	$('.js--close-modal').on('click', function(e){
		e.preventDefault();
		$(this).parents('.lightbox--modal').remove();
		$('html').removeClass('js--lightbox-open');
	});
}

function show_modal(obj){
       obj.slideToggle(300);
}

function display_error(error_msg){
	if (!error_msg){
		error_msg = "Uh oh. Something went wrong. Try refreshing the page and hope that it helps!"
	}
	var error_html = '<div class="banner banner--error isle wrap">' + error_msg + '</div>';
	$('body').prepend(error_html);
}

function send_error_msg(error_info){
	//TODO: include browser info and more relevant details
	error_msg = "something went wrong in function: " + error_info.func_name;
	data = {
		'error_msg': error_msg
	}
	$.ajax({
		data: data,
		url: '/send_error_msg',
		type: 'POST',
		success: function(){
			console.log('sent error message to team kudos')
		},
		error: function(){
			display_error();
			error_info = {
				'func_name': '/send_error_msg'
			}
			send_error_msg(error_info);
			console.log('failed sending error message to team kudos')
		}
	});
}

function get_tag_list(obj, post_id){
	//gets tag list from db to populate autocomplete for tag modals
	//obj must have tag_input class

	var data = {
		post_id: post_id
	}

	$.ajax({
		type: "POST",
		url: "/create_tag_list",
		data: data,
		success: function(tag_info){

			tag_words = tag_info.tag_words;
			tag_dict = tag_info.tag_dict;
			tag_ids = tag_info.tag_ids;

			// this makes the tag input work for all tag autocompleters. uses tagsinput.js
			obj.tagsInput({
				autocomplete_list: tag_words,
				autocomplete_dict: tag_dict,
				tag_ids: tag_ids,
			});
		},
		error: function(){
			display_error();
			error_info = {
				'func_name': '/create_tag_list'
			}
			send_error_msg(error_info);
		},
		dataType: 'json'
	});
};

function show_all_tags(post_id) {
        var result;
        var data = {
                post_id: post_id
        };

        $.ajax({
                url: '/tagged_in_post',
                type: 'POST',
                data: data,
                success: function(data) {
                        $('body').append(data);
                        $('html').addClass('js--lightbox-open');
                        prepModals();
                },
                error: function(message) {
                        console.log('Error fetching taggees for post #' + data.post_id);
                        console.log(message);
                        return false;
                }
        });

        return result;
};

window.initTagsModal = function($jqObject) {
	$jqObject.each(function(){
		$(this).off().on('click', function(e){
      e.preventDefault();
      var post_id = $(this).parents('.post[data-post-id]').data('post-id'),
          taggees = show_all_tags(post_id);
		});
	});
};

function collect_tags(form){
	//collects tags that you have chosen to submit with new post

	var all_tags = form.find("span.tag"); //gives you all tags in new post form
	$.each(all_tags, function(){
		var hidden_tag_ids = form.find(".hidden_tag_ids");
		var hidden_tag_text = form.find(".hidden_tag_text");
		var tag_id = $(this).attr('id');	//tag_id === user or team_id of chosen tag
		hidden_tag_ids.val(hidden_tag_ids.val() + tag_id + "|");
		var tag_text = $(this).children("span").text();
		hidden_tag_text.val(hidden_tag_text.val() + tag_text + "|");
	});
	console.log($(".hidden_tag_ids").val());
};

function show_progress(clicked_element){
	clicked_element.css('cursor', 'progress');
	$('body').css('cursor', 'progress');

}

function end_show_progress(clicked_element){
	clicked_element.css('cursor', 'default');
	$('body').css('cursor', 'default');
}

function clear_post_modal_info(){
	$('#post_body').text("");
	$('#post_body').attr('data-chars-remain', $('#post_body').attr('data-character-count'));
	$('.post-modal .tag_input').importTags('');
	$('.post__new-tagged span').remove();
	$('.hidden_tag_ids').val("");
	$('.hidden_tag_text').val("");
	$('#chosen').text("");
	$('.submit-kudos').removeClass('error-post');
	$('.dropbox-dropin-btn').removeClass('dropbox-dropin-success').addClass('dropbox-dropin-default');
};

$('#nav-feedback, .cancel-feedback-btn').on('click', function(e){
	e.preventDefault();
	$('.feedback-modal').toggleClass('displaying')
});

$('.submit-feedback-btn').on('click', function(e){
	e.preventDefault();
	console.log("in submit feedback");
	var feedback = $('.feedback-input').val();

	if(feedback == "") {
		$('.feedback-input').focus().addClass('error').one('webkitAnimationEnd mozAnimationEnd oAnimationEnd animationEnd', function(){
			$(this).removeClass('error');
		});
		return false;
	}

	var data = {
		feedback: feedback
	};

	$.ajax({
		type: "POST",
		url: "/feedback",
		data: data,
		success: function(response){
			$('.feedback-input').val("");
			$('.feedback-modal').removeClass('displaying');
		},
		error: function(){
			display_error();
			error_info = {
				'func_name': '/feedback'
			}
			send_error_msg(error_info);
			console.log("could not submit feedback");
		}
	});
});

//escape key to exit out of feedback modal
document.onkeydown = function(evt) {
	evt = evt || window.event;
	if (evt.keyCode == 27) {
		if ($('.feedback-modal').hasClass('displaying')){
			$('.feedback-modal').removeClass('displaying');
			$('.feedback-input').val("");
		}
	}
};

window.initCharCount = function($obj) {
	$obj.each(function(){
		$(this).attr('data-chars-remain', $(this).attr('data-character-count'))
		$(this).keyup(function(e){
			var chars = $(this).text().length;
			var limit = $(this).attr('data-character-count');
			count = limit - chars;
			$(this).attr('data-chars-remain', count);
			if( count <= 0 ) {
				$(this).addClass('js--invalid');
			} else {
				$(this).removeClass('js--invalid');
			}
		});
	});
};


//TAG MODAL
$('.addtag-button').live('click', function(e){
	e.preventDefault();
	var post_id = $(this).data('post-id');

	$('body').append('<div class="lightbox lightbox--modal cn-c tag-modal cf" data-post-id="' + post_id + '">\
        <form class="cn-w card card--modal island wrap new-tag-form" data-post-id="' + post_id + '">\
        	<i class="lightbox-close js--close-modal fa fa-times" title="Cancel"></i>\
          <div class="cf tags" data-post-id="' + post_id + '">\
            <input type="text" class="tag_input vi-hd" data-post-id="' + post_id + '"/>\
            <div data-id="_tagsinput" class="tagsinput h-m">\
              <div data-id="_addTag">\
                <input data-id="_tag" class="spit input span-all input--plain input--plain-highlight" value="" data-default="Who do you want to thank?" placeholder="Who do you want to thank?"/>\
              </div>\
            </div>\
            <button type="submit" class="f-r new-tag-btn in butt" data-post-id="' + post_id + '">Add tags</button>\
          </div>\
          <input id="hidden_post_id" name="hidden_post_id" type="hidden" value="' + post_id + '">\
          <input class="hidden_tag_ids" id="' + post_id + '" name="hidden_tag_ids" type="hidden" value="">\
          <input class="hidden_tag_text" id="' + post_id + '" name="hidden_tag_text" type="hidden" value="">\
        </form>\
      </div>');

$('html').addClass('js--lightbox-open');

	var tag_input = $('.tag_input[data-post-id=' + post_id + ']'),
	    tag_modal = $('.tag-modal[data-post-id=' + post_id + ']');

	prepModals();
	get_tag_list(tag_input, post_id);

});

//REMOVE TAG
$('.remove-tag').live('click', function(e) {
	e.preventDefault();
	var avatar = $(this).parent('.avatar-container'),
		post_id = $(this).parents('.post').data('post-id'),
		tag_id = avatar.data('tag-id'),
		data = {
			tag_id: tag_id
		};
	var user_id = ""
	var team_id = ""
	if ($('.user-card').data('user-id')){
		user_id = $('.user-card').data('user-id')
	}
	if ($('.team__title').data('team-id')){
		team_id = $('.team__title').data('team-id')
	}

	$.ajax({
		type: "POST",
		url: '/deletetag',
		data: data,
		success: function(tag_info){
			//remove post from user or team page if removing their tag
			if (tag_info.user_id == user_id){
				remove_post();
				return
			} else if (tag_info.team_id == team_id){
				remove_post();
				return
			}

			function remove_post(){
				post = $('.post[data-post-id=' + post_id +']');
				post.addClass('post--remove-from-stream');
				post.one('webkitAnimationEnd mozAnimationEnd oAnimationEnd animationEnd', function(){
					post.remove();
				});
				if ($('ol.posts').children('li').length == 1){
					change_to_no_posts_yet_title();
				}
			}

			replace_one_post(post_id);
		},
		error: function(){
			display_error();
			error_info = {
				'func_name': '/deletetag'
			}
			send_error_msg(error_info);
			console.log("error removing tag");
		},
		dataType: 'json'
	});

});


//SUBMIT NEW TAG
$('.new-tag-btn').live('click', function(e) {
	e.preventDefault();

	var form = $(this).parents('.new-tag-form');
	collect_tags(form);
	var	tag_ids = form.find('.hidden_tag_ids').val(),
		tag_text = form.find('.hidden_tag_text').val(),
		parent_post_id = $(this).data('post-id'),
		post_photo_url = form.parents('.post').closest('.post-photo[data-post-id="' + parent_post_id + '"]').attr('src'),
		post_text = form.parents('.post').children('.post__container').children('.post__content').children('.p').text();


	$('html').removeClass('js--lightbox-open');

	if (tag_ids != ""){
		var data = {
			parent_post_id: parent_post_id,
			tag_ids: tag_ids,
			tag_text: tag_text,
			post_photo_url: post_photo_url,
			post_text: post_text
		};

		$.ajax({
			type: "POST",
			data: data,
			url: '/newtag',
			success: function(tag_info){
				$('.js--close-modal').trigger('click');

				$.extend(data, {
					post_text: post_text,
					tagged_team_ids: JSON.stringify(tag_info.tagged_team_ids),
					tagged_user_ids: JSON.stringify(tag_info.tagged_user_ids)
				});

				replace_one_post(data.parent_post_id);
				send_notifications(data);
			},
			error: function(){
				console.log('error');
			},
			dataType: 'json'
		});
	}

	else{
		$(this).parent().append("<span> No new tags selected </span>");
		e.preventDefault();
		console.log('no new tags');
	}
});

function replace_one_post(post_id) {
	old_post = $('.post[data-post-id=' + post_id + ']');
	data = {'post_id': post_id};
	$.ajax({
		data: data,
		url: '/display_single_post',
		type: 'POST',
		success: function(new_post){
			old_post.before(new_post);
			initCommentButtons($('.post[data-post-id=' + post_id + ']'));
			initRemoveButton($('.post[data-post-id=' + post_id + '] .remove-post-button'));
			initTagsModal($('post[data-post-id=' + post_id + '] .js--show-all-taggees'));
			initRemoveComment($('post [data-post-id=' + post_id + '] .remove-comment'));
			old_post.remove();
		},
		error: function(){

		}
	});
}


//REMOVE COMMENT
window.initRemoveComment = function($jqObject) {
	$jqObject.each(function(){
		$(this).off().on('click', function(e){
			e.preventDefault();
			var post_id = $(this).data('comment-id');
			var parent_post_id = $(this).closest('.comments').data('post-id');
			var comment = $(this).parents('[data-comment-id=' + post_id + ']');
			data = {
				post_id: post_id
			};

			$.ajax({
				type: "POST",
				data: data,
				url: '/deletepost',
				success: function(comment_id){

					var remove = function(){
						comment.remove();
						$('#comment-body-' + parent_post_id).removeAttr('disabled').removeClass('no-w').addClass('g--two-thirds');
						$('.thanked[data-post-id=' + parent_post_id + ']').removeClass('span-all thanked').addClass('g--one-third comment-button').html('<i class="fa fa-heart"></i> Thank');
						initCommentButtons($('.post[data-post-id=' + parent_post_id + ']'));
					};

					if(animations.supported) {
						comment.addClass("js--comment-remove").one('webkitAnimationEnd oAnimationEnd mozAnimationEnd animationEnd', remove());
					} else {
						remove();
					}

					comment_count_selector = $('[data-post-id=' + parent_post_id + '] .comment-count');
					change_count(comment_count_selector, -1);

				},
				error: function(){
					display_error();
					error_info = {
						'func_name': '/deletepost'
					}
					send_error_msg(error_info);
				}
			});
		});
	});
};


//SUBMIT NEW COMMENT
window.initCommentButtons = function($jqObject){
	$jqObject.find('.comment-button').off().one('click', function(e){
	e.preventDefault();
	var new_comment_btn = $(this);
	var data = {
		parent_post_id: $(this).parents('.post').data('post-id'),
		post_text: $('#comment-body-' + $(this).parents('.post').data('post-id')).val()
	}

	var all_comments = $('.comments[data-post-id=' + data.parent_post_id + ']');
	show_progress($('.comment-button'));
	$.ajax({
		type: "POST",
		url: '/newcomment',
		data: data,
		success: function(response){
			if (response.is_error) {
				end_show_progress($('.comment-button'));
				display_error("Sorry! This post had already been removed.");
				return
			}

			all_comments.append(response.comment_template);
			all_comments.children('.one-comment').last().addClass('js--new-comment');

			comment_count_selector = $('[data-post-id=' + data.parent_post_id + '] .comment-count');
			change_count(comment_count_selector, 1);

			initRemoveComment($('[data-post-id=' + data.parent_post_id + '] .remove-comment'));

			//clear and hide comment modal
			new_comment_btn.addClass('thanked js--pressed span-all an-w').html('<i class="fa fa-heart"></i> Thanked');
			$('#comment-body-' + data.parent_post_id).addClass('an-w no-w').attr('disabled', 'true').val('');

			end_show_progress($('.comment-button'));
			if (data.post_text){
				$.extend(data, {
					tagged_team_ids: JSON.stringify(response.tagged_team_ids),
					tagged_user_ids: JSON.stringify(response.tagged_user_ids),
					is_comment: true
				})
				send_notifications(data);
			}
		},
		error: function(e){
			display_error();
			error_info = {
				'func_name': '/newcomment'
			}
			send_error_msg(error_info);
		},
		dataType: 'json'
	});
});
	return true;
}

$('.comment__input').each(function(){
	var parent_post_id = $(this).parents('[data-post-id]').data('post-id');
	$(this).keyup(function(e){
		if(e.keyCode == 13) {
			$('.comment-button[data-post-id=' + parent_post_id + ']').trigger('click');
		}
	});
});

function send_notifications(data){
	// data must include post_id, tagged_team_ids, tagged_user_ids, post_text, photo_url
	$.ajax({
		type: "POST",
		url: "/create_notifications",
		data: data,
		success: function(){
			console.log("success sending email notifications");
		},
		error: function(){
			display_error();
			error_info = {
				'func_name': '/create_notifications. failed sending.'
			}
			send_error_msg(error_info);
			console.log("failed sending email notifications");
		}
	});

}


// Focus post body
$('.js--hocus-focus').on('click', function(e){
	e.preventDefault();
	$('.post__new-content').focus();
});

function change_count(jquery_selector, add_value){
	//add or subtract counts on white card (ex thanks or comments)
	//jquery_selector is the <a> tag selector

	var text = jquery_selector.text();
	var count = parseInt(text.split(' ', 1)[0]);
	var subject = text.split(' ')[1]; //ie. thanks or comments

	var new_count = count + add_value;

	//remove plural s at end of subject if already there
	if (subject.slice(-1) === 's'){
		subject = subject.slice(0,-1);
	}

	if (new_count === 1){
		jquery_selector.text(new_count + ' ' + subject);
	}
	else{
		jquery_selector.text(new_count + ' ' + subject + 's');
	}
}


//Dropbox Chooser file selection
$(function () {
	var data = {};
	$('#chooser').on('DbxChooserSuccess', function (e) {
		console.log('chooser success');
		data = {
			url: e.originalEvent.files[0].link,
			filename: e.originalEvent.files[0].name,
			thumbnail: e.originalEvent.files[0].thumbnails["200x200"]
		};

		$('#chosen').show();
		$('#filename').text(data['filename']);
	});

	//Submit new post
	$('.submit-new-post').on('click', function(e){
		console.log('clickkkkk');
		//Check if file selected from dropbox chooser
		if ($.isEmptyObject(data)===false){
			console.log('not empty data')
			//can only send binary data using blob
			var xhr = new XMLHttpRequest();
			xhr.open("GET", data['thumbnail'], true);
			xhr.responseType = "blob";
			xhr.onload = function (oEvent)  {
				//handle errors in here
				var blob = xhr.response;
				s3_upload(
					{
					raw: blob,
			        filename: data['filename'],
			        type: xhr.getResponseHeader("Content-Type")},
			        function (public_url){
			        	create_post(public_url);
			        	//reset data={} so no picture uploaded with next post
			        	data = {};
			        }
		        );
			};
			xhr.send();
		}
		else{
			create_post();
		}
	});
});

// Create post
function create_post(public_url) {
	if ($('.new-post-form').hasClass('submitting')) {
		return;
	}
	$('.new-post-form').addClass('submitting');

	post_text = $('#post_body').text();

	data = {
		photo_url: public_url,
		post_text: post_text
	};

	if (!post_text || post_text.length > 500){
		$('.post__new-content').focus().addClass('error').one('webkitAnimationEnd mozAnimationEnd oAnimationEnd animationEnd', function(){
			$(this).removeClass('error');
		});
		$('.new-post-form').removeClass('submitting');
		return;
	}

	collect_tags($('.new-post-form'));

	$.extend(data, {
		hidden_tag_ids: $('.hidden_tag_ids').val() || $('.prefilled_tag_ids').val(),
		hidden_tag_text: $('.hidden_tag_text').val() || $('.prefilled_tag_text').val()
	});

	show_progress($('.submit-new-post'));
	$.ajax({
		type: "POST",
		url: "/createpost",
		data: data,
		success: function(response){
			// response includes post markup, and list of tagged team/user ids

			//if first post on user page, remove 'Why not be the first?'
			if ($('.no-posts').length > 0){
				$('.no-posts').hide();
				$('.no-posts').removeClass('no-posts');
				var full_name = data.hidden_tag_text;
				full_name = full_name.substring(0, full_name.length -1); // remove trailing '|' from hidden_tag_text
				var new_post_column = '<h2 class="gamma p post-column-title">Posts thanking ' + full_name + '</h2>\
									<ol class="posts post-column">' + response.new_post + '</ol>'
				$('.main-column').append(new_post_column)
			}

			else {
				$('.post-column').prepend(response.new_post);
			}
			initCommentButtons($('.post[data-post-id=' + response.post_id + ']'));
			initRemoveButton($('.post[data-post-id=' + response.post_id + '] .remove-post-button'));
			$('ol.posts .post').first().addClass('post--new-in-stream');
			clear_post_modal_info();
			end_show_progress($('.submit-new-post'));

			$.extend(data, {
				parent_post_id: response.post_id,
				tagged_team_ids: JSON.stringify(response.tagged_team_ids),
				tagged_user_ids: JSON.stringify(response.tagged_user_ids),
				is_new_post: true
			});

			initCommentButtons($('.post[data-post-id=' + data.parent_post_id + ']'));
			initRemoveButton($('.post[data-post-id=' + data.parent_post_id + '] .remove-post-button'));
			initTagsModal($('.post[data-post-id=' + data.parent_post_id + '] .js--show-all-taggees'));
			initRemoveComment($('.post[data-post-id=' + data.parent_post_id + '] .remove-comment'));

			$('.new-post-form').removeClass('submitting');

			if (data.tagged_team_ids || data.tagged_user_ids){
				// only send emails if users or teams tagged
				send_notifications(data);
			}

		},
		error: function(resp){
			display_error();
			error_info = {
				'func_name': '/createpost'
			}
			send_error_msg(error_info);

			end_show_progress($('.submit-new-post'));
			$('.new-post-form').removeClass('submitting');
		},
		dataType:'json'
	});
}

function change_to_no_posts_yet_title() {
	full_name = $('.prefilled_tag_text').val();
	full_name = full_name.substring(0, full_name.length -1); // remove trailing '|' from hidden_tag_text
	$('.post-column-title').remove();
	var post_column_title = '<p class="beta promo faded no-posts post-column-title">\
	No posts thanking ' + full_name + ' yet. Why not <a href="#" class="js--hocus-focus">\
	be the first?</a></p>'
	$('.main-column').append(post_column_title);
}

//REMOVE POST
window.initRemoveButton = function($jqObject) {
	$jqObject.each(function(){
		$(this).off().on('click', function(e){
			e.preventDefault();
			var post_id = $(this).closest('.post').data('post-id');
			var parent_post = $(this).closest('.post');
			data = {
				post_id : post_id
			}
			$.ajax({
				type: "POST",
				url: '/deletepost',
				data: data,
				success: function(resp){
					parent_post.addClass('post--remove-from-stream');
					if(animations.supported) {
						parent_post.one('webkitAnimationEnd mozAnimationEnd oAnimationEnd animationEnd', function(){
							$(this).remove();
						});
					} else {
						$(this).remove();
					}
					if ($('ol.posts').children('li').length == 1){
						change_to_no_posts_yet_title();
					}
					console.log("success deleting post");
				},
				error: function(resp){
					display_error();
					error_info = {
						'func_name': '/remove-post-button'
					}
					send_error_msg(error_info);
				}
			});
		});
	});
};

//Called if file chosen with dropbox chooser
function s3_upload(data, callback){
	console.log('in s3_upload');
	var public_url = ""

	var settings = {
        s3_sign_put_url: '/sign_s3_upload/',
        s3_object_name: data['filename'],

        onProgress: function(percent, message) {
            console.log("uploading file");
        },
        onFinishS3Put: function(public_url) {
            //Create preview of photo: $("#avatar_url").val(public_url);
            //$("#preview").html('<img src="'+public_url+'" style="width:300px;" />');
            console.log("finished uploading file");
            callback(public_url);
        },
        onError: function(status) {
        	console.log("error uploading file: " + status);
			display_error();
			error_info = {
				'func_name': 's3_upload in kudos.js'
			}
			send_error_msg(error_info);
        }
    };

    if (!data.raw) {
    	console.log("sending file dom data");
    	// TODO: this "file" selector should be configurable from 'data'
    	settings.file_dom_selector = "file";
    }
    else {
    	console.log("sending raw data: " + data.raw.length);
    	settings.raw_data = {data: data.raw, type: data.type};
    }

    var s3upload = new S3Upload(settings);
};

// Ready when you are

// Prepare tags input
$(document).ready(function(){
	tag_input = $('#new-post-tag-input');
	get_tag_list(tag_input);
	initCommentButtons($('.post[data-post-id]'));
	initCharCount($('[data-character-count]'));
	initRemoveButton($('.remove-post-button'));
	initTagsModal($('.js--show-all-taggees'));
	initRemoveComment($('.remove-comment'));
});

function call_collect_tags(){
	collect_tags($(this))
};

function collect_tags(form){

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
	clicked_element.css('cursor', 'progress');
	$('body').css('cursor', 'default');
}

function clear_post_modal_info(){
	$('#post_body').val("");
	$('.post-modal .tag_input').importTags('');
	$('.hidden_tag_ids').val("");
	$('.hidden_tag_text').val("");
	$('#chosen').text("");
	$('.submit-kudos').removeClass('error-post')
};

$('#nav-feedback').live('click', function(e){
	e.preventDefault();
	if ($('.feedback-modal').hasClass('displaying')){
		$('.feedback-modal').removeClass('displaying');
	}
	else{
		$('.feedback-modal').addClass('displaying');
	}
})

$('.submit-feedback-btn').live('click', function(e){
	e.preventDefault();
	console.log("in submit feedback");
	var feedback = $('.feedback-input').val();
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
			console.log("could not submit feedback");
		}
	})
})

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


$('.thank-button').live('click', function(e){
	e.preventDefault();
	var button = $(e.target);
	//REMOVE THANKS
	if (button.hasClass('pressed')){
		var data = {
			post_id: $(this).data('post-id')
		}
	 	$.ajax({
	 		type: 'POST',
	 		url: '/removethanks', 
	 		data: data,
	 		success: function(response){
	 			console.log("success removing thanks");
	 			button.removeClass('pressed');
	 		},
	 		error: function(){
	 			console.log("error removing thanks");
	 		}
	 	})
	}
	//SEND THANKS
	else{
		var data = {
          post_id: $(this).data('post-id')
        };
        $.ajax({
        	type: 'POST',
        	url: '/sendthanks',
        	data: data,
        	success: function(response){
        		console.log("success giving thanks");
		    	button.addClass('pressed');
        	},
        	error: function(){
        		console.log("error sending thanks");
        	}
        })
	}
});

//DISPLAY THANKERS
$('.thank-count').live('click', function(e){
	e.preventDefault()
	thanker_modal = $(this).parent().children('.thanker-modal').clone();
	thanker_modal.dialog({ title: "Thanks for your work!" });
})

//REMOVE TAG
$('.remove-tag').live('click', function(e) {
	e.preventDefault();
	var avatar = $(this).parent();
	var tagid = avatar.data('tag-id');
	var data = {
		tagid: tagid
	};


	$.ajax({
		type: "POST",
		url: '/deletetag/' + tagid,
		data: data,
		success: function(status){
			console.log(status);
			avatar.remove();
		},
		error: function(){
			console.log("error");
		}
	});
	
});


//ADD NEW TAG
$('.new-tag-btn').live('click', function(e) {
	e.preventDefault();
	form = $(this).parent('.new-tag-form');
	collect_tags(form);
	tag_ids = form.find('.hidden_tag_ids').val();
	tag_text = form.find('.hidden_tag_text').val();
	post_photo_url = form.parent('.tag-modal').parent('.post').children('.white-card').children('.post-photo').attr('src');
	post_text = form.parent('.tag-modal').parent('.post').children('.white-card').children('blockquote').text()

	if (tag_ids != ""){
		var data = {
		post_id: $(this).data('post-id'),
		tag_ids: tag_ids,
		tag_text: tag_text,
		post_photo_url: post_photo_url,
		post_text: post_text
		};

		$.post('/newtag', data, function(tag_info){
			form.parent().toggle(); 
			form.children('.tags').children('.tagsinput').children('span').remove(); //remove tag spans from input box
			form.children(".hidden_tag_ids").val(""); //and clear hidden values
			form.children(".hidden_tag_text").val("");
			console.log("tag_dict: " + tag_info);
			//turn tag_info json into usable array - avoidable if specify it's json datatype
			tag_array = jQuery.parseJSON(tag_info);

			//DISPLAY USER AVATARS
			for(var i = 0; i<tag_array.user_tags.length; i++){
				var username = $.trim(tag_array.user_tags[i].username);
				var user_id = tag_array.user_tags[i].user_id;
				var photo = tag_array.user_tags[i].photo;
				var new_avatar = $('<a class="avatar" href="/user/' + username + '"><div class="cropper"><img src=' + photo +' alt=' + username + '>');
				form.parent().parent().children(".taggees").children(".avatars").append(new_avatar);
			}

			//DISPLAY TEAM AVATARS
			for(var i = 0; i<tag_array.team_tags.length; i++){
				var teamname = tag_array.team_tags[i].teamname;
				var photo = tag_array.team_tags[i].photo;
				var new_avatar = $('<a class="avatar" href="/team/' + teamname + '""><div class="cropper"><img src=' + photo +' alt=' + teamname + '>');
				console.log("this" + this)
				form.parent().parent().children(".taggees").children(".avatars").append(new_avatar);
			}
		})
	}

	else{
		$(this).append("<span> No new tags </span>");
		e.preventDefault();
		console.log('no new tags');
	}

	
});

$('.addtag-button').live('click', function(e){
	e.preventDefault();
	$(this).parent().parent().children(".tag-modal").toggle();
	if ($(this).parents().siblings('.comment-modal').css('display') != 'none') {
		$(this).parent().parent().children('.comment-modal').toggle();
	};

});

$('.no_new_tag_btn').live('click', function(e){
e.preventDefault();
$(this).parent().toggle();
})

//SHOW COMMENT MODAL
$('.comment-button').live('click', function(e){
	e.preventDefault();
	$(this).parent().parent().children(".comment-modal").toggle();
	if ($(this).parents().siblings('.tag-modal').css('display') != 'none') {
			$(this).parent().parent().children('.tag-modal').toggle();
		};
});

//NEW POST MODAL
$('.cancel-new-post').live('click', function(e) {
	$('.post-modal').toggle();
	$('.post-column').css('margin', '0px');
	clear_post_modal_info()
});

$('.new-post-modal-btn').live('click', function(e) {
	$('.post-modal').toggle();
});


//REMOVE COMMENT
$('.remove-comment').live('click', function(e){
	e.preventDefault();
	var post_id = $(this).data('post-id');
	var comment = $(this).parent().parent()
	var data = {

	}

	$.ajax({
		type: "POST",
		url: '/deletepost/' + post_id,
		data: data,
		success: function(post_id){
			comment.remove();
			console.log("success");
			//TODO: reduce number of comments by 1

		}, 
		error: function(){
			console.log("error");
		}
	})
})

//NEW COMMENT
$('.new-comment-btn').live('click', function(e){
	e.preventDefault();
	var new_comment_btn = $(this)
	var data = {
		post_id: $(this).parent().data('post-id'),
		body: $(this).siblings('.reply-body').val()
	}
	console.log(data);
	//get entire comment display to append new comment to
	var comment_display=$(this).parent().parent().parent().parent().children('.comments');

	$.ajax({
		type: "POST",
		url: '/newcomment',
		data: data, 
		success: function(comment_info){
			console.log("sucess - new comment submitted");

			var username = comment_info.author_username
			var photo = comment_info.author_photo
			var id = comment_info.comment_id
			var author_name = comment_info.author_name
			var new_comment = $('<div class="one-comment" id="' + id + '"><div class="clearfix"><a class="avatar" href="/user/"' + username + '"><div class="cropper"><img src=' + photo +' alt=' + username + '></div></a><span class="comment-body">' + data["body"] + '</span><a href="/user/' + username + '" class="comment-author">' + author_name + '</a><div class="remove-comment" id="' + id + '><a href="#">Remove</a></div></div></div>');

			comment_display.append(new_comment);

			new_comment_btn.siblings('.reply-body').val("");
			new_comment_btn.parent().parent().parent('.comment-modal').toggle()

		},
		error: function(e){
			console.log('error creating new reply')
		},
		dataType: "json"
	});
})

//Dropbox Chooser file selection
$(function () {
	var data = {};
	//.live is same as .on() for earlier jquery versions
	$('#chooser').live('DbxChooserSuccess', function (e) {
		console.log('chooser success');
		//e.preventDefault();
		data = {
			url: e.originalEvent.files[0].link,
			filename: e.originalEvent.files[0].name,
			thumbnail: e.originalEvent.files[0].thumbnails["200x200"]
		};

		$('#chosen').show();
		$('#filename').text(data['filename']);
		$('#submit').attr('disabled', false);			
		
	});
	$('#remove').live('click', function (e) {
		e.preventDefault();
		data = {}
		$('#chosen').hide();
		$('.dropbox-chooser').removeClass('dropbox-chooser-used');
		$('#submit').attr('disabled', true);
	});

	//Submit new post
	$('.submit-new-post').live('click', function(e){
		show_progress($(this));
		//Check if file selected from dropbox chooser
		if ($.isEmptyObject(data)===false){
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
			        }
		        );
			};
			xhr.send();
		}
		else{
			create_post();
		}
		end_show_progress($(this));
	});	
});

function create_post(public_url){
	collect_tags($('.new-post-form'));
	post_body = $('#post_body').val()

	if (!post_body){
		$('.submit-kudos').addClass('error-post');

	}
	data = {
		public_url: public_url,
		post_body: post_body,
		hidden_tag_ids: $('.hidden_tag_ids').val(),
		hidden_tag_text: $('.hidden_tag_text').val()
	}

	$.ajax({
		type: "POST", 
		url: "/createpost",
		data: data, 
		success: function(new_post){
			$('.post-column').prepend(new_post);
			$('.post-modal').toggle();
			$('.post-column').css('margin', '0px');
			clear_post_modal_info();
			console.log("success! created new post");
		},
		error: function(resp){
			console.log("error! no new post created");
		}
	});
}


//REMOVE POST
$('.remove-post-button').live('click', function(e){
	e.preventDefault();
	var post_id = $(this).parent().parent('.post').data('post-id');
	var parent_post = $(this).parent().parent('.post');
	data = {
		post_id : post_id
	}
	$.ajax({
		type: "POST",
		url: '/deletepost/' + post_id,
		data: data,
		success: function(resp){
			parent_post.remove();
			console.log("success deleting post");
		},
		error: function(resp){
			console.log("error deleting post");
		} 
	})

});

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




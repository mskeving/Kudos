function call_collect_tags(){
	collect_tags($(this))
}

function collect_tags(form){

	var all_tags = form.find("span.tag"); //gives you all tags in new post form 
	$.each(all_tags, function(){
		var hidden_tag_ids = form.find(".hidden_tag_ids");
		var hidden_tag_text = form.find(".hidden_tag_text");
		var tag_id = $(this).attr('id');
		hidden_tag_ids.val(hidden_tag_ids.val() + tag_id + "|");
		var tag_text = $(this).children("span").text();
		hidden_tag_text.val(hidden_tag_text.val() + tag_text + "|");
	});
	console.log($(".hidden_tag_ids").val());
}

$('.thank-button').click(function(e){
	e.preventDefault();
	var button = $(e.target);
	//REMOVE THANKS
	if (button.hasClass('pressed')){
		var data = {
			post_id: this.id
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
          post_id: this.id
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
})



//REMOVE TAG
$('.remove-tag').click(function(e) {
	e.preventDefault();
	var avatar = $(this).parent();
	var tagid = avatar.attr('id')
	console.log("tagid: " + tagid)
	var data = {
		tagid: tagid
	}


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
$('.new-tag-btn').click(function(e) {
	e.preventDefault();
	console.log('clicked to add tags for: ' + this.id);
	form = $(this).parent()
	collect_tags(form);
	tag_ids = form.find('.hidden_tag_ids').val();
	tag_text = form.find('.hidden_tag_text').val();

	if (tag_ids != ""){
		var data = {
		post_id: this.id,
		tag_ids: tag_ids,
		tag_text: tag_text
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
				var url = '{{url_for("user", username="mskeving")}}'
				new_url = url.replace("mskeving", username)
				var photo = tag_array.user_tags[i].photo;
				var new_avatar = $('<a class="avatar" id=' + user_id + ' href=' + new_url + '><div class="cropper"><img src=' + photo +' alt=' + username + '>');
				console.log("this" + this)
				form.parent().parent().children(".taggees").children(".avatars").append(new_avatar);

			}
			//DISPLAY TEAM AVATARS
			for(var i = 0; i<tag_array.team_tags.length; i++){
				var teamname = tag_array.team_tags[i].teamname;
				var photo = tag_array.team_tags[i].photo;
				var url = '{{url_for("team", team="Baratheon")}}'
				var new_url = url.replace("Baratheon", teamname)
				var new_avatar = $('<a class="avatar" href=' + new_url + '><div class="cropper"><img src=' + photo +' alt=' + teamname + '>');
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

$('.addtag-button').click(function(e){
	e.preventDefault();
	$(this).parent().parent().children(".tag-modal").toggle();
	if ($(this).parents().siblings('.comment-modal').css('display') != 'none') {
		$(this).parent().parent().children('.comment-modal').toggle();
	};

});

$('.no_new_tag_btn').click(function(e){
e.preventDefault();
$(this).parent().toggle();
})

//SHOW COMMENT MODAL
$('.comment-button').click(function(e){
	e.preventDefault();
	$(this).parent().parent().children(".comment-modal").toggle();
	if ($(this).parents().siblings('.tag-modal').css('display') != 'none') {
			$(this).parent().parent().children('.tag-modal').toggle();
		};
});




$('#no-new-post-button').click(function(e) {
	//hide post modal and remove any input (post body, tags, or chosen images)
	$('.post-modal').toggle();
	$('#post_body').val("");
	$(this).parent().children('.tags').children('.tagsinput').children('span').remove();
	$('#chosen').text("");
	$('#post-column').css('margin', '0px');
});

$('#new-post-modal-btn').click(function(e) {
	$('.post-modal').toggle();
	if($('.post-modal').css('display')=='none'){
		$('#post-column').css('margin', '0px');
	}
	else{
		$('#post-column').css('margin', '240px 0px 0px 0px');
	};
});

//NEW POST - fill in with #new-post-button
$('#nothing').click(function(e){
	console.log("new post button")
	e.preventDefault();
	collect_tags($('.new_post_form'))
	var data = {
		post_body: $('#new_post_body').val(),
		hidden_tag_ids: $('.hidden_tag_ids').val(),
		hidden_tag_text: $('.hidden_tag_text').val(),
		photo_info: $('.dropbox-chooser').val()
	};
	console.log(data);
	$.ajax({
		type: 'POST',
		url: '/editpost',
		data: data,
		success: function(e){
			//html for new post
			console.log("success - new comment submitted");
		},
		error: function(e){
			console.log('error creating new post');
		}
	});
	

});

//REMOVE COMMENT
$('.remove-comment').click(function(e){
	e.preventDefault();
	var post_id = $(this).attr('id');
	var comment = $(this).parent().parent()
	var data = {

	}

	$.ajax({
		type: "POST",
		url: '/deletepost/' + post_id,
		data: data,
		success: function(response){
			comment.remove();
			console.log("success");
		}, 
		error: function(){
			console.log("error");
		}
	})
})

//NEW COMMENT
$('.new-comment-btn').click(function(e){
	console.log("in fnc")
	e.preventDefault();
	console.log("in new comment button function");
	var data = {
		post_id: $(this).parent().attr('id'),
		body: $(this).siblings('.reply-body').val()
	}
	console.log(data);
	//get entire comment display to append new comment to
	var comment_display=$(this).parent().parent().parent().parent().siblings('"' + data['post_id'] + '.comments');

	$.ajax({
		type: "POST",
		url: '/newcomment',
		data: data, 
		success: function(comment_info){
			console.log("sucess - new comment submitted");

			var username = comment_info.author_username
			var photo = comment_info.author_photo
			var id = comment_info.comment_id
			var new_avatar = '<a class="avatar" href="{{url_for("user", username="' + username + '")}}"><div class="cropper"><img src=' + photo +' alt=' + username + '>';
			var new_comment = $('<div class="one-comment" id="' + id + '"><div class="clearfix">' + new_avatar) 

			comment_display.append(new_comment);
			//two separate appends to close <a> tag? DOESN'T WORK! 
			new_comment=$('"#' + id + '.one-comment');

			new_comment.append($('<span class="comment-body">' + data["body"] + '<br>'));


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
	$('#remove').click(function (e) {
		e.preventDefault();
		data = {}
		$('#chosen').hide();
		$('.dropbox-chooser').removeClass('dropbox-chooser-used');
		$('#submit').attr('disabled', true);
	});

	//Submit new post
	$('#new-post-button').click(function(e){
		//Check if file selected from dropbox chooser
		if ($.isEmptyObject(data)===false){
			//can only send binary data using blob
			var xhr = new XMLHttpRequest();
			xhr.open("GET", data['thumbnail'], true);
			xhr.responseType = "blob";
			xhr.onload = function (oEvent)  {
				//handle errors in here
				var blob = xhr.response;
				s3_upload({raw: blob,
				        filename: data['filename'],
				        type: xhr.getResponseHeader("Content-Type")},

				        function (public_url){
					       	collect_tags($('.new_post_form'));
							data = {
								public_url: public_url,
								post_body: $('#post_body').val(),
								hidden_tag_ids: $('.hidden_tag_ids').val(),
								hidden_tag_text: $('.hidden_tag_text').val(),
							};
							$.ajax({
								type: "POST", 
								url: "/editpost",
								data:data, 
								success: function(e){
									console.log("success! created new post");
								},
								error: function(e){
									console.log("error! no new post created");
								}
							});

				        });
				};
			}
			else{
				collect_tags($('.new_post_form'));
			data = {
				post_body: $('#post_body').val(),
				hidden_tag_ids: $('.hidden_tag_ids').val(),
				hidden_tag_text: $('.hidden_tag_text').val(),
			};
			$.ajax({
				type: "POST", 
				url: "/editpost",
				data:data, 
				success: function(e){
					console.log("success! created new post");
				},
				error: function(e){
					console.log("error! no new post created");
				}
			});

			};

			xhr.send();
		
	});	



});

function s3_upload(data, callback){
	console.log("DATA HERE!!!!!")
	console.log(data)
	console.log('in s3_upload');
	var public_url = ""

	// call new endpoint
	//data['filename'] = 'secret.jpg';

	// don't call this guy
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


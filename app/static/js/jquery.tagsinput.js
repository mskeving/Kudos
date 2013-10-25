/*

	jQuery Tags Input Plugin 1.3.3
	
	Copyright (c) 2011 XOXCO, Inc
	
	Documentation for this plugin lives here:
	http://xoxco.com/clickable/jquery-tags-input
	
	Licensed under the MIT license:
	http://www.opensource.org/licenses/mit-license.php

	ben@xoxco.com

*/

(function($) {

	var delimiter = new Array();
	var tags_callbacks = new Array();
	$.fn.doAutosize = function(o){
	    var minWidth = $(this).data('minwidth'),
	        maxWidth = $(this).data('maxwidth'),
	        val = '',
	        input = $(this),
	        testSubject = $('#'+$(this).data('tester_id'));
	
	    if (val === (val = input.val())) {return;}
	
	    // Enter new content into testSubject
	    var escaped = val.replace(/&/g, '&amp;').replace(/\s/g,' ').replace(/</g, '&lt;').replace(/>/g, '&gt;');
	    testSubject.html(escaped);
	    // Calculate new width + whether to change
	    var testerWidth = testSubject.width(),
	        newWidth = (testerWidth + o.comfortZone) >= minWidth ? testerWidth + o.comfortZone : minWidth,
	        currentWidth = input.width(),
	        isValidWidthChange = (newWidth < currentWidth && newWidth >= minWidth)
	                             || (newWidth > minWidth && newWidth < maxWidth);
	
	    // Animate width
	    if (isValidWidthChange) {
	        input.width(newWidth);
	    }



  };
  $.fn.resetAutosize = function(options){
    // alert(JSON.stringify(options));
    var minWidth =  $(this).data('minwidth') || options.minInputWidth || $(this).width(),
        maxWidth = $(this).data('maxwidth') || options.maxInputWidth || ($(this).closest('.tagsinput').width() - options.inputPadding),
        val = '',
        input = $(this),
        testSubject = $('<tester/>').css({
            position: 'absolute',
            top: -9999,
            left: -9999,
            width: 'auto',
            fontSize: input.css('fontSize'),
            fontFamily: input.css('fontFamily'),
            fontWeight: input.css('fontWeight'),
            letterSpacing: input.css('letterSpacing'),
            whiteSpace: 'nowrap'
        }),
        testerId = $(this).attr('id')+'_autosize_tester';
    if(! $('#'+testerId).length > 0){
      testSubject.attr('id', testerId);
      testSubject.appendTo('body');
    }

    input.data('minwidth', minWidth);
    input.data('maxwidth', maxWidth);
    input.data('tester_id', testerId);
    input.css('width', minWidth);
  };
  
	$.fn.addTag = function(value,options,settings) {
		options = jQuery.extend({focus:false,callback:true},options);
		
		this.each(function() { 
			var id = $(this).attr('id');
			
			//get index of tag in autocomplete_list
			// var tag_position = jQuery.inArray(value, settings.autocomplete_list);
			//find corresponding tag_id in tag_ids array
			// var tag_id = settings.tag_ids[tag_position];
			settings = settings || $(this).data('tag-settings');
			var tag_id = settings.autocomplete_dict[value];	

			var tagslist = $(this).val().split(delimiter[id]);
			//var tagslist = JSON.parse($(this).val());
			//tagslist needs tag object appended to it 
			if (tagslist[0] == '') { 
				tagslist = new Array();
			}

			value = jQuery.trim(value);
			//go through word list and find value's index. Then go through tag_objects list and find value at same index
			//add that to html element as value 

			var skipTag;
			if (options.unique) {
				if (skipTag = $(this).tagExist(value)) {
					//Marks fake input as not_valid to let styling it
				    $('#'+id+'_tag').addClass('not_valid');
				}
			} else {
				var skipTag = false; 
			}
			
			//add id to each new tag, specific to person or team tagged
			if (value !='' && skipTag != true) { 
                $('<span>').attr('id',tag_id).addClass('tag').append(
                    $('<span>').text(value).append('&nbsp;&nbsp;'),
                    $('<a>', {
                        href  : '#',
                        title : 'Removing tag',
                        text  : 'x'
                    }).click(function () {
                        return $('#' + id).removeTag(escape(value));
                    })
                ).insertBefore('#' + id + '_addTag');

				tagslist.push(value);
			
				$('#'+id+'_tag').val('');
				if (options.focus) {
					$('#'+id+'_tag').focus();
				} else {		
					$('#'+id+'_tag').blur();
				}
				
				$.fn.tagsInput.updateTagsField(this,tagslist);
				
				if (options.callback && tags_callbacks[id] && tags_callbacks[id]['onAddTag']) {
					var f = tags_callbacks[id]['onAddTag'];
					f.call(this, value);
				}
				if(tags_callbacks[id] && tags_callbacks[id]['onChange'])
				{
					var i = tagslist.length;
					var f = tags_callbacks[id]['onChange'];
					f.call(this, $(this), tagslist[i-1]);
				}					
			}
	
		});		
		
		return false;
	};
		
	$.fn.removeTag = function(value) { 
			value = unescape(value);
			this.each(function() {
				var id = $(this).attr('id');
	
				var old = $(this).val().split(delimiter[id]);
				$('#'+id+'_tagsinput .tag').remove();
				str = '';
				for (i=0; i< old.length; i++) { 
					if (old[i]!=value) { 
						str = str + delimiter[id] +old[i];
					}
				}
				$.fn.tagsInput.importTags(this,str);

				if (tags_callbacks[id] && tags_callbacks[id]['onRemoveTag']) {
					var f = tags_callbacks[id]['onRemoveTag'];
					f.call(this, value);
				}
			});
					
			return false;
		};
	
	$.fn.tagExist = function(val) {
		var id = $(this).attr('id');
		var tagslist = $(this).val().split(delimiter[id]);
		return (jQuery.inArray(val, tagslist) >= 0); //true when tag exists, false when not
	};
	
	// clear all existing tags and import new ones from a string
	$.fn.importTags = function(str) {
        var id = $(this).attr('id');
		$('#'+id+'_tagsinput .tag').remove();
		$.fn.tagsInput.importTags(this,str);
	}
		
	$.fn.tagsInput = function(options, obj) {

		//$(this) is the class tag_input
		var default_settings = {
	      interactive:true,
	      defaultText:'add a tag',
	      minChars:0,
	      width:'300px',
	      height:'100px',
	      autocomplete: {selectFirst: false },
	      hide:true,
	      delimiter:',',
	      unique:true,
	      removeWithBackspace:true,
	      placeholderColor:'#666666',
	      autosize: true,
	      comfortZone: 20,
	      inputPadding: 6*2
		}
	    var settings = jQuery.extend(default_settings, options);
	    $(this).data('tag-settings', settings);

		this.each(function() { 

			if (settings.hide) { 
				$(this).hide();				
			}
			var id = $(this).attr('id');
			if (!id || delimiter[$(this).attr('id')]) {
				id = $(this).attr('id', 'tags' + new Date().getTime()).attr('id');
			}
			
			var data = jQuery.extend({
				pid:id,
				real_input: '#' + id,
				holder: '#' + id + '_tagsinput',
				input_wrapper: '#' + id + '_addTag',
				fake_input: '#' + id + '_tag'
			}, settings);
	
			delimiter[id] = data.delimiter;
			
			if (settings.onAddTag || settings.onRemoveTag || settings.onChange) {
				tags_callbacks[id] = new Array();
				tags_callbacks[id]['onAddTag'] = settings.onAddTag;
				tags_callbacks[id]['onRemoveTag'] = settings.onRemoveTag;
				tags_callbacks[id]['onChange'] = settings.onChange;
			}

			//instead of creating new markup, add unique ids to already exisitng 
			$(this).siblings('.tagsinput').attr('id', id + '_tagsinput');
			$(this).siblings('.tagsinput').children('[data-id=_addTag').attr('id', id + '_addTag');
			$(this).siblings('.tagsinput').children('[data-id=_addTag').children('[data-id=_tag]').attr('id', id + '_tag');


	
			if ($(data.real_input).val()!='') { 
				$.fn.tagsInput.importTags($(data.real_input),$(data.real_input).val());
			}		
			if (settings.interactive) { 
				$(data.fake_input).val($(data.fake_input).attr('data-default'));
				$(data.fake_input).css('color',settings.placeholderColor);
		        $(data.fake_input).resetAutosize(settings);
		
				$(data.holder).bind('click',data,function(event) {
					$(event.data.fake_input).focus();
				});
			
				$(data.fake_input).bind('focus',data,function(event) {
					if ($(event.data.fake_input).val()==$(event.data.fake_input).attr('data-default')) { 
						$(event.data.fake_input).val('');
					}
					$(event.data.fake_input).css('color','#000000');		
				});
						
				if (settings.autocomplete_dict != undefined) {
					autocomplete_options = jQuery.extend(
						{source: settings.autocomplete_list},
						settings.autocomplete
					);
				
					$(data.fake_input).autocomplete(autocomplete_options);
					$(data.fake_input).bind('autocompleteselect',data,function(event,ui) {
						tokentext = ui.item.value;
						$(event.data.real_input).addTag(tokentext,{focus:true,unique:(settings.unique)}, settings);
						return false;
					});
				} else {
						// if a user tabs out of the field, create a new tag
						// this is only available if autocomplete is not used.
						$(data.fake_input).bind('blur',data,function(event) { 
							var d = $(this).attr('data-default');
							if ($(event.data.fake_input).val()!='' && $(event.data.fake_input).val()!=d) { 
								if( (event.data.minChars <= $(event.data.fake_input).val().length) && (!event.data.maxChars || (event.data.maxChars >= $(event.data.fake_input).val().length)) )

									$(event.data.real_input).addTag($(event.data.fake_input).val(),{focus:true,unique:(settings.unique)});
							} else {
								$(event.data.fake_input).val($(event.data.fake_input).attr('data-default'));
								$(event.data.fake_input).css('color',settings.placeholderColor);
							}
							return false;
						});
				
				}
				// if user types a comma, create a new tag
				$(data.fake_input).bind('keypress',data,function(event) {
					if (event.which==event.data.delimiter.charCodeAt(0) || event.which==13 ) {
					    event.preventDefault();
					    var tokentext = $(event.data.fake_input).val();
						if( (event.data.minChars <= tokentext.length) && (!event.data.maxChars || (event.data.maxChars >= tokentext.length)) ) {
							$(event.data.real_input).addTag(tokentext,{focus:true,unique:(settings.unique)});
						}
					  	$(event.data.fake_input).resetAutosize(settings);
						return false;
					} else if (event.data.autosize) {
			            $(event.data.fake_input).doAutosize(settings);
            
          			}
				});
				//Delete last tag on backspace
				data.removeWithBackspace && $(data.fake_input).bind('keydown', function(event)
				{
					if(event.keyCode == 8 && $(this).val() == '')
					{
						 event.preventDefault();
						 var last_tag = $(this).closest('.tagsinput').find('.tag:last').text();
						 var id = $(this).attr('id').replace(/_tag$/, '');
						 last_tag = last_tag.replace(/[\s]+x$/, '');
						 $('#' + id).removeTag(escape(last_tag));
						 $(this).trigger('focus');
					}
				});
				$(data.fake_input).blur();
				
				//Removes the not_valid class when user changes the value of the fake input
				if(data.unique) {
				    $(data.fake_input).keydown(function(event){
				        if(event.keyCode == 8 || String.fromCharCode(event.which).match(/\w+|[áéíóúÁÉÍÓÚñÑ,/]+/)) {
				            $(this).removeClass('not_valid');
				        }
				    });
				}
			} // if settings.interactive
		});
			
		return this;
	
	};
	
	$.fn.tagsInput.updateTagsField = function(obj,tagslist) { 
		var id = $(obj).attr('id');
		$(obj).val(tagslist.join(delimiter[id]));
	};
	
	$.fn.tagsInput.importTags = function(obj,val) {			
		$(obj).val('');
		var id = $(obj).attr('id');
		var tags = val.split(delimiter[id]);
		for (i=0; i<tags.length; i++) {

			$(obj).addTag(tags[i],{focus:false,callback:false});
		}
		if(tags_callbacks[id] && tags_callbacks[id]['onChange'])
		{
			var f = tags_callbacks[id]['onChange'];
			f.call(obj, obj, tags[i]);
		}
	};

})(jQuery);

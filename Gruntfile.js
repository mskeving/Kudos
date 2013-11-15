module.exports = function(grunt) {
	pkg: grunt.file.readJSON('package.json'),
	grunt.initConfig({
		// Sass
		sass: {
		  dist: {
		  	options: {
		  		sourcemap: true,
		  		compass: true
		  	},
		    files: {
		    	// 'output.css' : 'input.scss'
		        'app/static/css/style.css' : 'app/static/sass/style.scss'
		    }
		  }
		},
		// Auto-prefix CSS properties using Can I Use?
	  autoprefixer: {
	    options: {
	    	// Last 2 versions of all browsers, plus IE7/8, BB10 (LOL), and Android 3+
	    	browsers: ['last 2 versions', 'ie 8', 'ie 7', 'bb 10', 'android 3']
	    },
	    no_dest: {
	    	// File to output
	      src: 'app/static/css/style.css',
	    },
	  },
	  csso: {
      dist: {
      	options: {
      		banner: '/*# sourceMappingURL=style.css.map */'
      	},
        files: {
        	// Output compressed CSS to style.min.css
          'app/static/css/style.min.css': ['app/static/css/style.css']
        }
      }
    },
    // Watch files for changes
    watch: {
      css: {
        files: ['app/static/sass/style.scss'],
        // Run Sass, autoprefixer, and CSSO
        tasks: ['sass', 'autoprefixer', 'csso'],
        options: {
          spawn: false,
        },
      },
    }
	});

	// Register our tasks
	grunt.loadNpmTasks('grunt-contrib-watch');
	grunt.loadNpmTasks('grunt-autoprefixer');
	grunt.loadNpmTasks('grunt-contrib-sass');
	grunt.loadNpmTasks('grunt-csso');
	grunt.registerTask('default', ['watch']);
};
ngds.Search = function() {
	var package_extras='';

	ngds.subscribe('Map.area_selected',function(msg,data){
		if(data['type']==='rectangle') {
			bbox = new ngds.Map.BoundingBox();
			bbox.construct_from_leaflet_shape(data['feature']['rect']);
			package_extras = {
				'ext_bbox':bbox.get_bbox_array().join(',')
			};
		}
		else if(data['type']==='polygon'){
			var coords = [];
			$.each(data['feature']['poly']._latlngs,function(index,item){
					coords.push([item.lat,item.lng]);
			});
			package_extras = {
				'poly':coords
			}
		}
	});

	var me = this;
	var pager_div = $(".search-results-page-nums");

	var go_to = function(params) {
		var q ='';
		var rows = params['rows'];
		var action = params['action'];
		var page = params['page'];
		ngds.Map.cur_page = page;
		var start = (page - 1) * rows;

		if(typeof params['q'] === 'undefined') {
			q = me._q;
		}
		else {
			me._q = params['q'];
		}
		ngds.Map.current_query = me._q;
		ngds.log("Searching for term : "+q+", rows : "+rows+", page : "+page+" start : "+start);
		if(package_extras==='') {
			var southWest = new L.LatLng(-90, -180),
		    northEast = new L.LatLng(90, 180),
		    bounds = new L.LatLngBounds(southWest, northEast);
			bbox = new ngds.Map.BoundingBox();
			bbox.store_raw(bounds);
			package_extras = {
				'ext_bbox':bbox.get_bbox_array().join(',')
			};
		}

		action({
			'rows':rows,
			'q':q,
			'start':start,
			'extras':package_extras
		},function(response){
			ngds.publish('Map.results_received',{
				'results':response.result.results,
				'query':ngds.Map.current_query,
				'count':response.result.count
			});
			var num_pages = Math.ceil(response.result.count/rows);
			var pager_div = $(".search-results-page-nums");
			// $(".results").addClass("full");
			for(var i=1;i<num_pages+1;i++) {
				var a_to_append = ngds.util.dom_element_constructor({
					'tag':'a',
					'attributes':{
						'class':'page-num',
						'text':i
					}
				});
				pager_div.append(a_to_append);

				if(parseInt(ngds.Map.cur_page)===i) {
					var a=a_to_append;
					a.addClass("page-active");
				}
			}			
		});

	};

	return {
		'go_to':go_to
	}
};
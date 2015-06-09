# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import settings
import sys

def connection():
    ''' User this function to create your connections '''
    import sys
    sys.path.append(settings.MADIS_PATH)
    import madis

    con = madis.functions.Connection('articles.db')
    
    return con

# Create a new connection
con=connection()

# --------------------------------------------------------------------------------------------------

def classify(pubid, topn):

    # Create a cursor on the connection
    cur = con.cursor()

    cur.execute('select summary from articles where id = ?', [(pubid)])
    sel = cur.fetchall()
    if len(sel) == 0:
        return [("id - does not exist in DB",),]

    try:
        int(topn)
    except ValueError:
        return[("WrongInput.at(Top N classes - should be integer)",),]

    if  int(topn) < 0:
        return[("WrongInput.at(Top N classes - should be positive integer)",),]

    res = [("title", "class", "subclass", "sum")]

    cur.execute(        "   select var('id', ? )					", (pubid,));
    cur.execute(        "   select var('n', ? )                     ", (topn,));
    sel = cur.execute(  "   select 									"
    					"		s.title, 							"
    					"		c.class, 							"
    					"		c.subclass, 						"
    					"		sum(c.weight) as sumw 				"
                        "   from 									"
                        "		classes c,							"
                        "       (									"	
                        "			select 							"
                        "				title, 						"
                        "				strsplitv(summary) as spl   "
                        "       	from 							"
                        "				articles                    "
                        "       	where 							"
                        "				id = var('id')				"
                        "		) s                         		"
                        "   where 									"
                        "		c.term = s.spl                      "
                        "   group by 								"
                        "		s.title, 							"
                        "		c.class, 							"
                        "		c.subclass               			"
                        "   order by sumw desc             			"
                        "   limit var('n')                          ")
    for i in sel:
        res.append(i)

    return res

# --------------------------------------------------------------------------------------------------
def getKey(item):
    return item[3]

def classify_plain_sql(pubid, topn):

    # Create a cursor on the connection
    cur = con.cursor()

    cur.execute(' select 			'
    			'	a.title        	'
                ' from 				'
                '	articles a      '
                ' where 			'
                '	a.id = ?		', [pubid])
    title = cur.fetchall()
    if len(title) == 0:
        return [("id - does not exist in DB",),]

    try:
        int(topn)
    except ValueError:
        return[("WrongInput.at(Top N classes - should be integer)",),]

    if int(topn) < 0:
        return[("WrongInput.at(Top N classes - should be positive integer)",),]

    res = []

    cur.execute(' select distinct	'
    			' 	c.class, 		'
    			'	c.subclass 		'
                ' from 				'
                '	classes c    	')

    # classes_subclasses has two columns referred to every class and subclass
    classes_subclasses = cur.fetchall()
    # Get the summary of the given article
    summary = cur.execute(	' select 		'
    						'	a.summary   '
                      		' from 			'
                      		'	articles a  '
                      		' where 		'
                      		'	a.id = ?	', [pubid])
    for i in summary:
    	# Split the summary into words
        words = i[0].split()

    for cs in classes_subclasses:
        weights = 0
        for word in words:
            weightl = cur.execute(	' select 				'
            						'	c.weight            '
                               		' from 					'
                               		'	classes c           '
                               		' where 				'
                               		'	c.class = ? and 	'
                               		'	c.subclass = ? and 	'
                               		'	c.term = ?			'
                               		, [cs[0], cs[1], word])
            for z in weightl:
            	# Sum the weight of terms included in words
                weights = weights + z[0]
                
        if weights != 0:
            res.append((title[0][0], cs[0], cs[1], weights))

    # Sort results - the biggest sum is shown first
    res = sorted(res, key=getKey, reverse=True)

    # Find topn sums
    res = res[:int(topn)]
    return [("title", "class", "subclass", "sum")] + res

# --------------------------------------------------------------------------------------------------

def updateweight(class1, subclass, term, weight):

    # Create a cursor on the connection
    cur = con.cursor()

    cur.execute(' select 				'
    			'	*              		'
                ' from 					'
                '	classes c           '
                ' where 				'
                '	c.class = ? and 	'
                '	c.subclass = ? and 	'
                '	c.term = ?   		',
                [class1, subclass, term])

    sel = cur.fetchall()
    if len(sel) == 0:
        return [("WrongInput.at(Class or Subclass or Term)",), ]

    try:
        float(weight)
    except ValueError:
        return[("WrongInput.at(Weight - should be float)",),]

    cur.execute(' update 						'
    			'	classes 					'
    			' set 							'
    			'	weight = (weight + ?)/2     '
                ' where 						'
                '	class = ? and 				'
                '	subclass = ? and 			'
                '	term = ?         			',
                [float(weight), class1, subclass, term])

    return [("ok",), ]

# --------------------------------------------------------------------------------------------------

def selectTopNauthors(class1,n):
	
    # Create a cursor on the connection
    cur=con.cursor()

    cur.execute(' select *         '
                ' from classes c   '
                ' where c.class = ?',[class1])

    sel = cur.fetchall()
    if len(sel) == 0:
        return [("WrongInput.at(Class - does not exist in DB)",), ]

    try:
        int(n)
    except ValueError:
        return[("WrongInput.at(N - should be integer)",),]

    if int(n) < 0 :
        return[("WrongInput.at(N - should be positive integer)",),]

    cu = cur.execute(	' select 												'
						'  	authors.id, 										'
						' 	count(distinct articles.id) as numberOfpapers 		'
						' from 													'
						'  	articles, 											'
						'  	authors_has_articles, 								'
						'	authors, 											'
						' 	article_has_class  									'
						' where 												'
						'	articles.id = authors_has_articles.articles_id and 	'
						'	authors.id = authors_has_articles.authors_id and 	'
						'	article_has_class.article_id = articles.id and 		'
						'	article_has_class.class = ? 						'
						' group by authors.id									'
						' order by numberOfpapers desc 							'
						' limit ?; 												',[class1,n])

    L = [("authorId", "numberOfpapers")]
    for idd,sums in cu:
    	L.append((idd,sums))
    return L

# --------------------------------------------------------------------------------------------------

def findSimilarArticles(articleId,n):

    # Create a cursor on the connection
    cur=con.cursor()

    cur.execute("select * from articles where id = ?",[articleId])
    sel = cur.fetchall()
    if len(sel) == 0:
        return [("WrongInput.at(articleId - does not exist in DB)",), ]

    try:
        int(n)
    except ValueError:
        return[("WrongInput.at(N similar articles - should be integer)",),]
    if int(n) < 0 :
        return[("WrongInput.at(N similar articles - should be positive integer)",),]

    cur.execute("select var('articleId', ? )", (articleId,))
    cur.execute("select var('n', ? )", (n,))
    article_ids = cur.execute(	" select    											"
								"	a1.aid,    											"
								"	a2.aid,    											"
								"  	jaccard(a1.wgroup, a2.wgroup) as similarity    		"
								" from    												"
								" (    													"
								" 	select      										"
								"		aid,     										"
								"		jgroup(word) as wgroup     						"
								"	from     											"
								"	(    												"
								"		select     										"
								"			article.id as aid,    						"
								"			strsplitv(article.summary) as word     		"
								"		from     										"
								"			articles article    						"
								"		group by article.id,word    					"
								"	) as id_words_table    								"
								"	where 												"
								"		word not in 									"
								" 		(												"
								"   	  	select  									"
								"				findcommonterms(articles.summary)		"
								"		  	from										"
								"				articles								"
								"		) 												"
								"	group by aid    									"
								" ) as a1,    											" 
								" (    													"
								" 	select      										"
								"		aid,     										"
								"		jgroup(word) as wgroup     						"
								"	from     											"
								"	(    												"
								"		select     										"
								"			article.id as aid,    						"
								"			strsplitv(article.summary) as word     		"
								"		from     										"
								"			articles article    						"
								"		group by article.id,word    					"
								"	) as id_words_table    								"
								"	where 												"
								"		word not in 									"
								" 		(												"
								"   	  	select  									"
								"				findcommonterms(articles.summary)		"
								"		  	from										"
								"				articles								"
								"		) 												"
								"	group by aid    									"
								" ) as a2    											"  
								" where    												"
								"	a1.aid = var('articleId') and 						"
								"	a1.aid != a2.aid    								"
								" order by similarity desc 								"
								" limit var('n');										")
    

    L = [("article1id","article2id","jaccard")]
    for id1,id2,j in article_ids:
        L.append((id1,id2,j))
    return L
    
# --------------------------------------------------------------------------------------------------

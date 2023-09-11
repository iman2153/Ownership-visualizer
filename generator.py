import pandas as pd
import numpy as np
import squarify as sq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import base64
import io
df = pd.read_csv('megacorp_db.csv')

def build_hierarchical_arrays(df,depth,corp,x,y,width,height,colors,rects,black,text):
    
    df = df[df.child != 'Self'] # remove "self" references from initial database
    dfg = df.groupby('parent')
    
    # check to see if the corporation is in the db, otherwise set it to Default
    in_db = df['parent'].str.contains(corp) # Returns a series of len(dataframe) of boolean values
    if in_db.sum() == 0:
        corp = 'Default'
    
    # print out the initial corp to screen to make sure I'm doing the right one.
    print('corp = ')
    print(corp)
    
    # Get all the child data from the db
    get_corp = dfg.get_group(corp).sort_values(by=['ownership'], ascending=False)
    
    ## Build arrays
    # build a relative sizes array for this depth
    sizes = get_corp['ownership']
    sizes = np.array(sizes.values.tolist())
    sizes = sq.normalize_sizes(sizes, width, height)
    
    # create array of hashes with x,y,dx,dy for each child corp
    rects = sq.squarify(sizes, x, y, width, height)    
    
    # build colors array
    colors = get_corp['color'].to_list()
    
    # build labels array
    labels = get_corp['child'].to_list()
    
    # Make labels wrap by putting in newlines if words are long (because I can't get "wrap=True" to work)
    if text and depth == 0: labels = wrap_labels(labels)

    # Build the above arrays for each depth, replacing the level above at each step
    for i in range(depth):
        sizes, rects, colors, labels = remap_corp(df, sizes, rects, colors, labels, black, text)    
        
    return sizes, rects, colors, labels
def remap_corp(df, sizes, rects, colors, labels, black, text):

    # Iterate through children nodes to create sub arrays, replacing each 
    # parent entry with its child sub array
    for i, child in enumerate(labels): 
        # Skip "self"
        if child == 'Self':
            continue
        
        dfg = df.groupby('parent')

        # check to see if the corporation is in the db, otherwise set it to Default
        in_db = df['parent'].str.contains(child)
        if in_db.sum() == 0:
            child = 'Default'
        
        # specific one off function to show Blackrock ownership by just replacing Merrill Lynch
        #if not child == 'Merrill Lynch Co Inc':
        #    continue
        
        # Get the dimensions of the current square from rects
        dims = rects[i]
        x, y, dx, dy = dims['x'], dims['y'], dims['dx'], dims['dy']
        get_corp = dfg.get_group(child).sort_values(by=['ownership'], ascending=False)
        
        ## Build arrays for each child
        # build a relative sizes array for this depth
        sizes = get_corp['ownership']
        sizes = np.array(sizes.values.tolist())
        sizes = sq.normalize_sizes(sizes, dx, dy)

        # create array of hashes with x,y,dx,dy for each child corp
        rects[i] = sq.squarify(sizes, x, y, dx, dy)

        # build colors sub array for child
        colors_temp = get_corp['color'].to_list()
        # set to black all corps not retail or insider if black flag is true
        # i.e. all corps with children that would become black with more iterations
        if black:
            if not child == 'Retail' or not child == 'Insider':
                for j, color in enumerate(colors_temp):
                    if not color == '#ffffff': # 'or' didn't work here?
                        if not color == '#797979':
                            colors_temp[j] = '#000000'        
        
        colors[i] = colors_temp
            
        # build labels sub array for child
        labels[i] = get_corp['child']
    
    # Flatten all arrays
    
    # Use smart_flat in case of multiple layers of array 
    # (e.g. looking at just Merrill Lynch for Blackrock in remap_corp)
    rects = [val for sublist in rects for val in sublist]
    colors = [val for sublist in colors for val in sublist]
    labels = [val for sublist in labels for val in sublist]
    
    # If there are partial sublists use smart_flat
    #rects = smart_flat(rects)
    #colors = smart_flat(colors)
    #labels = smart_flat(labels)
    
    return sizes, rects, colors, labels
def get_self(df, corp):
    corp_group = df.loc[df['parent'] == corp]
    colors = corp_group.loc[corp_group['child'] == 'Self']['color'].to_list()
    sizes = [1]
    sizes = sq.normalize_sizes(sizes, 1, 1)
    rects = sq.squarify(sizes, 0, 0, 1, 1)
    labels = [corp]

    return sizes, rects, colors, labels

def smart_flat(lst):
    new_list = []
    for sublist in lst:
        if isinstance(sublist, list):
            for val in sublist:
                new_list.append(val)
        else:
            new_list.append(sublist)
    return new_list
def wrap_labels(labels_ary):
    for i, label in enumerate(labels_ary):
        label_temp = label.split()
        for j, word in enumerate(label_temp):
            if len(word) > 3: # Adjust word length as required
                if not j == len(label_temp)-1:
                    label_temp[j] = word + '\n'
            else:
                label_temp[j] = word + ' '
        labels_ary[i] = "".join(label_temp)
    return labels_ary
def bright_enough(face_color):
    str = face_color
    label_color = '#000000'
    # get r g b values from color
    r = int(str[1:3],16)
    g = int(str[3:5],16)
    b = int(str[5:7],16)
    # get luminosity values. Adjust r g b thresholds for white text on color as desired
    luma = 0.134 * r + 0.125 * g + 0.147 * b
    # adjust luma threshold as needed
    if (luma < 10):
        label_color = '#ffffff'
    
    return label_color

def generate_treemap(corp_name, depth=0, text=True, black=False, self_flag=False):
    corp = corp_name
    width = 1
    height = 1
    x = 0
    y = 0
    rects = []
    colors = []
    labels = []

    if self_flag:
        sizes, rects, colors, labels = get_self(df, corp)
    else:
        sizes, rects, colors, labels = build_hierarchical_arrays(df, depth, corp, x, y, width, height, colors, rects, black, text)

    fig = plt.figure(figsize=(15, 15))
    axes = [fig.add_axes([rect['x'], rect['y'], rect['dx'], rect['dy']]) for rect in rects]

    if text: 
        labels = wrap_labels(labels)

    for ax, color, label in zip(axes, colors, labels):
        ax.set_facecolor(color)
        label_color = bright_enough(color)
        if text:
            fontsize = 36 if self_flag else 18
            dy = ax.bbox.height / 1000
            dx = ax.bbox.width / 1000
            bottom = 0.05 if dy < 0.06 else 0.1 if dy < 0.1 else 0.3 if dy < 0.2 else 0.4 if dy < 0.3 else 0.5
            if dx > 0.08:
                ax.text(.5, bottom, label, fontsize=fontsize, ha="center", c=label_color, wrap=True)
        ax.xaxis.set_ticks([])
        ax.yaxis.set_ticks([])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()  # Close the plot to free up memory
    return img_data



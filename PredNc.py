#!/usr/bin/env python
docstring='''
PredNc.pl seq.ss2 seq.solv
    predict the number contacts for short (6<=|i-j|<12),
    medium (12<=|i-j|<24), long (24<=|i-j|), and all (6<=|i-j|) range.

    Notice that the definition of "long" range is NOT the same as that
    used by NeBcon.

input files:
    seq.ss2  - stage 2 secondary structure prediction by PSIPRED 4.
    seq.solv - solvent accessibility prediction by "solvpred" program
               from metapsicov.

option:
    -atom={CB,CA,feat}
        CB   - (default) C alpha contact
        CA   - C beta contact
        feat - print feature values instead of predicted contact numnber
    
    -use_prob={true,false}
        true - use psipred probability for counting ss composition
        false - use predicted ss for counting ss composition

    -model=1,2,4,8
        1 - (default) helix, strand, coil, accessibility, bias
        2 - helix, other (nonhelix), accessibility, bias
        4 - helix, strand, coil, bias
        8 - L, bias
'''

import sys
import re

psipred_pat=re.compile("\s*\d+\s+[A-Z]\s+([A-Z])\s+([.\d]+)\s+([.\d]+)\s+([.\d]+)\s*$")
solvpred_pat=re.compile("\s*\d+\s+[A-Z]\s+([.\d]+)\s*$")

feat_list=["helix","strand","coil","other","l","acc","bias"]
range_list=["short","medm","long","all"]

PredNc_dict={
    1:{
    'feat':["helix","strand","coil","acc","bias"],
    'CA':[#helix,strand,coil,acc,bias,RMSE/L
         [0.17,0.58,0.41,-0.39, 4.80,0.11], # short
         [0.10,1.05,0.51,-0.62, 8.57,0.18], # medm
         [1.89,2.91,2.90,-5.08, 1.01,0.25], # long
         [2.16,4.53,3.82,-6.10,14.38,0.18], # all
         ],
    'CB':[#helix,strand,coil,acc,bias,RMSE/L
         [0.23,0.55,0.47,-0.49, 6.43,0.11], # short
         [0.23,1.03,0.60,-0.82,12.38,0.18], # medm
         [2.53,3.33,3.37,-6.00,-4.42,0.34], # long
         [3.00,4.91,4.43,-7.31,14.40,0.34], # all
         ],
    },

    2:{
    'feat':["helix","other","acc","bias"],
    'CA':[#helix,other,acc,bias,RMSE/L
         [0.15,0.99,-0.44, 5.92,0.10], # short
         [0.02,1.57,-0.78,12.23,0.18], # medm
         [1.89,5.80,-5.08, 1.08,0.25], # long
         [2.06,8.36,-6.30,19.23,0.19], # all
         ],
    'CB':[#helix,other,acc,bias,RMSE/L
         [0.22,1.02,-0.51, 7.02,0.11], # short
         [0.17,1.63,-0.94,15.34,0.18], # medm
         [2.54,6.70,-5.99,-4.65,0.34], # long
         [2.93,9.35,-7.45,17.71,0.35], # all
         ],
    },

    4:{
    'feat':["helix","strand","coil","bias"],
    'CA':[#helix,strand,coil,bias,RMSE/L
         [ 0.10,0.52,0.32, -0.92,0.11], # short
         [-0.02,0.95,0.37, -0.44,0.18], # medm
         [ 0.93,2.13,1.75,-72.73,0.30], # long
         [ 1.00,3.60,2.44,-74.09,0.29], # all
         ],
    'CB':[#helix,strand,coil,bias,RMSE/L
         [ 0.14,0.48,0.36, -0.68,0.11], # short
         [ 0.08,0.90,0.41,  0.50,0.18], # medm
         [ 1.40,2.41,2.01,-91.54,0.37], # long
         [ 1.61,3.80,2.78,-91.72,0.41], # all
         ],
    },

    8:{
    'feat':["l","bias"],
    'CA':[#  L,  bias,RMSE/L
         [0.26,  3.51,0.13], # short
         [0.30,  9.68,0.24], # medm,
         [1.45,-59.84,0.37], # long,
         [2.00,-46.65,0.53], # all
         ],
    'CB':[# L,   bias,RMSE/L
         [0.28,  2.93,0.11], # short,
         [0.35,  9.09,0.21], # medm,
         [1.81,-80.75,0.35], # long,
         [2.44,-68.73,0.48], # all,
         ],
    },
}

def get_PredNc_feat(ss_file="seq.ss2",solv_file="seq.solv",use_prob=True):
    ''' generate features from input secondary structure 
    and solvent accessibility prediction '''
    feat_dict={"bias":1}
    for feat in feat_list:
        feat_dict[feat]=0
    feat_dict["bias"]=1

    fp=open(ss_file,'rU')
    txt=fp.read()
    fp.close()

    for line in txt.splitlines():
        match_list=psipred_pat.findall(line)
        if len(match_list):
            SS,C,H,E=match_list[0]
            feat_dict['l']+=1
            if use_prob:
                feat_dict["helix"]+=float(H)
                feat_dict["strand"]+=float(E)
                feat_dict["coil"]+=float(C)
                feat_dict["other"]+=(1-float(H))
            else:
                feat_dict["helix"]+=(SS=='H')
                feat_dict["strand"]+=(SS=='E')
                feat_dict["coil"]+=(SS=='C')
                feat_dict["other"]+=(SS!='H')

    fp=open(solv_file,'rU')
    txt=fp.read()
    fp.close()
    L=0
    for line in txt.splitlines():
        match_list=solvpred_pat.findall(line)
        if len(match_list):
            L+=1
            feat_dict["acc"]+=float(match_list[0])
    if L!=feat_dict["l"]:
        sys.stderr.write("ERROR! %s and %s does not have the same length.\n"%
            (ss_file,solv_file))
    return feat_dict

def PredNc_from_feat(feat_dict,model=1,atom="CA"):
    ''' predict contact number from features '''
    Nc_dict=dict()
    for sep in range_list:
        Nc_dict[sep]=[]

    for m in sorted(PredNc_dict.keys(),reverse=True):
        if model>=m:
            for s,sep in enumerate(range_list):
                Nc_dict[sep].append(0)
                for f,feat in enumerate(PredNc_dict[m]["feat"]):
                    w=PredNc_dict[m][atom][s][f]
                    Nc_dict[sep][-1]+=w*feat_dict[feat]
            model-=m

    for s,sep in enumerate(range_list):
        Nc_dict[sep]=max([0,sum(Nc_dict[sep])/len(Nc_dict[sep])])
    return Nc_dict

if __name__=="__main__":
    atom="CB"
    model=1
    use_prob=True # whether to use cscore for psipred
    argv=[]
    for arg in sys.argv[1:]:
        if arg.startswith("-atom="):
            atom=arg[len("-atom="):]
        elif arg.startswith("-model="):
            model=int(arg[len("-model="):])
        elif arg.startswith("-use_prob="):
            use_prob=(arg[len("-use_prob="):].lower()=="true")
        elif arg.startswith("-"):
            sys.stderr.write("ERROR! Unknown argument %s\n"%arg)
            exit()
        else:
            argv.append(arg)

    if len(argv)!=2:
        sys.stderr.write(docstring)
        exit()

    feat_dict=get_PredNc_feat(argv[0],argv[1],use_prob)
    if atom=="feat":
        sys.stderr.write('\t'.join(feat_list)+'\n')
        sys.stdout.write('\t'.join(["%.1f"%feat_dict[feat
            ] for feat in feat_list])+'\n')
    else:
        Nc_dict=PredNc_from_feat(feat_dict,model,atom)
        sys.stderr.write('\t'.join(range_list)+'\n')
        sys.stdout.write('\t'.join(["%.1f"%Nc_dict[sep
            ] for sep in range_list])+'\n')
        

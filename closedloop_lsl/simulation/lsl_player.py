import mne_lsl
import numpy as np

def ampli_player(raw_fnames, chunk_size=33, n_repeat=np.inf):
    
    n_ampli = len(raw_fnames)
    amp_labels = np.arange(25, 25 + n_ampli)
    sources_id = np.arange(1, 1 + n_ampli)
    
    amplifiers = []
    for r, l, s in zip(raw_fnames, amp_labels, sources_id):
        name = f'EE225-000000-0006{l}'
        source = f'amp_{s}'
        amplifiers.append(mne_lsl.player.PlayerLSL(fname=r, 
                                                   chunk_size=chunk_size,
                                                   n_repeat=n_repeat,
                                                   name=name,
                                                   source_id=source))
    
    no_exit = True
    while no_exit:
        if not amplifiers[0].running:
            print("\nStarting LSL servers, press 'ctrl + c' to exit.\n")
            for amp in amplifiers:
                amp.start()
        
    return


if __name__ == '__main__':
    # raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/four_ampli/amp1-raw.fif',
    #               '/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/four_ampli/amp2-raw.fif',
    #               '/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/four_ampli/amp3-raw.fif',
    #               '/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/four_ampli/amp4-raw.fif']
    
    # raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/four_ampli/amp1-raw.fif']
    
    # mne_lsl player /home/jerry/python_projects/space/closedloop/test_data/TweakDreams/TD010_N1_64-raw.fif -c 33 -n EE225-000000-000625
    
    # raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/TD010_N1_64-raw.fif']
    # raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/TD006_N3_64-raw.fif']
    # raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/TD019_N2_64-raw.fif']
    raw_fnames = ['/home/jerry/python_projects/space/closedloop/test_data/TweakDreams/TD019_N2_64_mastoids-raw.fif']
    
    ampli_player(raw_fnames=raw_fnames)
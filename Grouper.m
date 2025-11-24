%%-----------------------------------------------------------
%  READ CSV & PLOT NODES
%%-----------------------------------------------------------

raw = readmatrix("/Users/ahilnandankabilan/Downloads/new 2/output_nodes.csv");

t = raw(:, 1);             
node_cols = raw(:, 3:end); 

nodeNames = { ...
    "N_0_0_1","N_0_1_1","N_0_2_1","N_0_3_1", ...
    "N_1_0_1","N_1_1_1","N_1_2_1","N_1_3_1", ...
    "N_2_0_1","N_2_1_1","N_2_2_1","N_2_3_1", ...
    "N_3_0_1","N_3_1_1","N_3_2_1","N_3_3_1" ...
};

figure;
plot(t, node_cols, 'LineWidth', 1.1);
grid on;
xlabel("Time (s)");
ylabel("Voltage (V)");
title("SPICE Output Node Voltages vs Time");
legend(nodeNames, 'Location', 'bestoutside');


%%-----------------------------------------------------------
%  PHASE EXTRACTION
%%-----------------------------------------------------------

function [phase_deg, T] = extract_phase(time, voltage, threshold)

    if nargin < 3
        threshold = 0.5;
    end

    rising = [];

    for i = 1:length(voltage)-1
        if voltage(i) < threshold && voltage(i+1) >= threshold
            t_cross = time(i) + (threshold - voltage(i)) * ...
                (time(i+1)-time(i)) / (voltage(i+1)-voltage(i));
            rising(end+1) = t_cross; %#ok<AGROW>
        end
    end

    if length(rising) < 6
        phase_deg = NaN;
        T = NaN;
        return;
    end

    SS = 5;
    rising_ss = rising(end-SS:end);

    T = median(diff(rising_ss));
    t_last = rising_ss(end);

    phase_rad = mod(t_last, T) / T * 2*pi;
    phase_deg = phase_rad * 180/pi;
end


function phases = compute_all_phases(time, node_cols, nodeNames)
    phases = struct();
    for k = 1:size(node_cols, 2)
        v = node_cols(:, k);
        [ph_deg, T] = extract_phase(time, v);
        phases.(nodeNames{k}) = ph_deg;
    end
end


%%-----------------------------------------------------------
%  RUN PHASE EXTRACTION
%%-----------------------------------------------------------

phases = compute_all_phases(t, node_cols, nodeNames);
disp("PHASES (degrees):");
disp(phases);


%%-----------------------------------------------------------
%  APPLY SIGNUM( COS(phase) )
%%-----------------------------------------------------------

phase_signum = struct();
fields = fieldnames(phases);

for i = 1:length(fields)
    name = fields{i};
    ph = phases.(name);
    phase_signum.(name) = sign(cosd(ph));
end

disp("SIGN( COS(phase) ) per node:");
disp(phase_signum);


%%-----------------------------------------------------------
%  WRITE SIGNUM VALUES TO CSV
%%-----------------------------------------------------------

output_path = "/Users/ahilnandankabilan/Downloads/new 2/signum_output.csv";

% Convert struct → table
node_list = fieldnames(phase_signum);
values = zeros(length(node_list), 1);

for i = 1:length(node_list)
    values(i) = phase_signum.(node_list{i});
end

T = table(node_list, values, 'VariableNames', {'Node', 'Signum'});

writetable(T, output_path);

fprintf("CSV written to: %s\n", output_path);
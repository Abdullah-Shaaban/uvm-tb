module alu(
    input  logic        clk_i,
    input  logic        arst_n_i,
    // Input interface
    input  logic        valid_i,
    output logic        ready_o,
    input  logic [31:0] a_i,
    input  logic [31:0] b_i,
    input  logic [3:0]  opcode_i,
    // Output interface
    output logic        valid_o,
    input  logic        ready_i,
    output logic [31:0] result_o
);

    // Internal signals
    logic [31:0] res;
    logic [31:0] result_reg;

    // Ready/Valid control logic
    always_ff @(posedge clk_i or negedge arst_n_i) begin
        if (!arst_n_i) begin
            valid_o <= 1'b0;
            ready_o <= 1'b0;
        end else begin
            if (valid_i && ready_o) begin // We accepted an input
                ready_o <= 1'b0; // Not ready until output is consumed
                valid_o <= 1'b1; // Output is valid. Single cycle operation
            end else if (valid_o && ready_i) begin // Our output was consumed
                ready_o <= 1'b1; // Ready to accept new input
                valid_o <= 1'b0; // Output consumed
            end else begin // No input or output
                ready_o <= 1'b1;
            end
        end
    end

    // Combinational logic
    always_comb begin
        case(opcode_i)
            4'b0000: res = a_i + b_i;
            4'b0001: res = a_i - b_i;
            4'b0010: res = a_i & b_i;
            4'b0011: res = a_i | b_i;
            4'b0100: res = a_i ^ b_i;
            4'b0101: res = a_i << b_i;
            4'b0110: res = a_i >> b_i;
            4'b0111: res = a_i * b_i;
            4'b1000: res = a_i / b_i;
            default: res = 32'b0;
        endcase
    end

    // Result register
    always_ff @(posedge clk_i or negedge arst_n_i) begin
        if (!arst_n_i) begin
            result_reg <= '0;
        end else begin
            result_reg <= res;
        end
    end

    assign result_o = result_reg;

endmodule

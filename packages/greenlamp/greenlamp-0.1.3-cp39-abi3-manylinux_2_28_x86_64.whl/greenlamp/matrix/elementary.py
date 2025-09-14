# Question 10 in python package greenlamp
import torch
# Rowswap function
def rowswap(input_mat, s_row, t_row):
    # Swap content of source row with target row
    # Above, for making copies, ChatGPT clarified how tensors are referenced in memory, stating that they reference each other directly (like a pointer)
    source_row = input_mat[s_row].clone() # Solution: make copies
    target_row = input_mat[t_row].clone()
    
    input_mat[s_row] = target_row
    input_mat[t_row] = source_row



# quick testbench
A = torch.tensor([[1,2,3], [4,5,6], [6, 7, 8]])
rowswap(A, 0, 2)
print("Rowswap: ", A)


# Rowscale function
def rowscale(input_mat, s_row, s_factor):
  # Scale the source row by the scaling factor
  source_row = input_mat[s_row].clone()
  input_mat[s_row] = s_factor*source_row
  return input_mat


# quick testbench
A = torch.tensor([[1,2,3], [4,5,6], [6, 7, 8]])
new_A = rowscale(A, 0, 5)
print("Rowscale: ", new_A)

# Row-replacement function
def rowreplacement(input_mat, f_row, s_row, s_factor_j, s_factor_k):
  # Form of R_i <- jR_i + kR_j (not stated in problem, but assumption)
  # f_row is index of R_i row
  # s_row is index of R_j row
  r_i = input_mat[f_row].clone()
  r_j = input_mat[s_row].clone()

  input_mat[f_row] = (s_factor_j*r_i) + (s_factor_k*r_j)
  return input_mat

# testbench
B = torch.tensor([[1,2,3], [4,5,6], [6,7,8]])
new_B = rowreplacement(B, 0, 1, 2, 1)
print("Rowreplacement: ", new_B)

# RREF Function
def rref(input_mat):
  # First, check that the first pivot (0,0) isn't 0
  found_pivot = False
  size = input_mat.size()
  num_rows = size[0]
  num_cols = size[1]
  print("num_rows: ", num_rows)
  print("num_cols: ", num_cols)
  i=0
  while input_mat[0][0] == 0 and i < size[0]-1:
    rowswap(input_mat, 0, i) # swap rows until not 0
    i += 1
  if input_mat[0][0] == 0:
    print("Error, first element is 0 in all rows")
  
  # Going to try column outer loop, row inner loop
  j=0
  k=0
  p_index=0
  e = 1e-20
  while j < num_cols:
    print("Value of k before entering loop: ", k)
    while k < num_rows:
      # Finding pivot loop (start of loop k is next possible pivot)
      if input_mat[k][j] > e: # Finding pivot (added e here for removing floating point instability in python)
        found_pivot = True
        rowscale(input_mat, k, 1/input_mat[k][j]) # normalize to 1
        p_index = k # set pivot index
        break
      else:
        k += 1
    # If no pivot found, found a column with all zeros
    if not found_pivot:
      j += 1
      continue # continue to next column

    found_pivot = False # reset pivot found
    k = 0 # restart k iterator
    while k < num_rows: # iterator k based on p_index
      # Set everything else in row on that column besides the pivot to 0
      if k != p_index:
        rowreplacement(input_mat, k, p_index, 1, -input_mat[k][j])
      k += 1
    k = p_index+1
    j += 1


# testbench
# Tested a few cases, ChatGPT helped me debug and catch the case of not finding a pivot due to a zero
# in the column as well as the "e" variable for helping with floating point instability.

# RREF Explanation:
'''
To begin, my idea was to iterate through all columns in an outer loop and rows in the inner loop. First, we need to make sure that the first pivot (0,0)
isn't 0, so the first while loop handles that. Next, I iterate through all columns, with the first inner loop finding the pivot, marking it
in the variable p_index and setting the found_pivot variable true. If that found pivot isn't true, then I know that column was zeros (for valid pivot indexes, go to next col).
Then, in the 2nd inner loop, we set every row of the pivot column equal to 0. Finally, we set k as the next valid pivot index and go to the next column.

As stated above, I used ChatGPT to debug this for edge cases, like the case of zero columns. Also seemed to be instability issues with floating point values, fixed with the 
comparison of the e variable
'''
test_mat = torch.tensor([[0,3,-6,6,4], [3,-7,8,-5,8], [3,-9,12,-9,6]], dtype=float)
rref(test_mat)
print(test_mat)
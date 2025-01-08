import math

class RestaurantNode:
    def __init__(self, name, stars, comment_nums):
        self.name = name        
        self.rating = self.calculate_rating(stars, comment_nums)
        self.left = None        
        self.right = None     
        self.height = 1
    
    def calculate_rating(self, stars, comment_nums):
        if comment_nums == 0:
            return 3.0

        weighted_score = (stars - 3.0) * (comment_nums / 1500)  # 控制評論數量對評分的影響
        rating = 3 + math.tanh(weighted_score) * 2  # 使用 tanh 函數調整評分範圍

        return round(max(1, min(5, rating)), 3)


class RestaurantAVL:
    def __init__(self):
        self.root = None

    def add_restaurant(self, name, stars, comment_nums):
        new_node = RestaurantNode(name, stars, comment_nums)
        self.root = self._insert(self.root, new_node)

    def _insert(self, current, new_node):
        if not current:
            return new_node

        if new_node.rating < current.rating:
            current.left = self._insert(current.left, new_node)
        elif new_node.rating > current.rating:
            current.right = self._insert(current.right, new_node)
        else:
            # 忽略相同評分的情況
            return current


        current.height = 1 + max(self._get_height(current.left), self._get_height(current.right))
        balance = self._get_balance(current)

        # LL
        if balance > 1 and new_node.rating < current.left.rating:
            return self._rotate_right(current)

        # RR
        if balance < -1 and new_node.rating > current.right.rating:
            return self._rotate_left(current)

        # LR
        if balance > 1 and new_node.rating > current.left.rating:
            current.left = self._rotate_left(current.left)
            return self._rotate_right(current)

        # RL
        if balance < -1 and new_node.rating < current.right.rating:
            current.right = self._rotate_right(current.right)
            return self._rotate_left(current)

        return current

    def _rotate_left(self, z):
        y = z.right
        T2 = y.left

        y.left = z
        z.right = T2

        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y

    def _rotate_right(self, z):
        y = z.left
        T3 = y.right

        y.right = z
        z.left = T3

        z.height = 1 + max(self._get_height(z.left), self._get_height(z.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y

    def _get_height(self, node):
        if not node:
            return 0
        return node.height

    def _get_balance(self, node):
        if not node:
            return 0
        return self._get_height(node.left) - self._get_height(node.right)
    
    def _inorder_traversal(self, node):
        if not node:
            return []
        return self._inorder_traversal(node.left) + [node] + self._inorder_traversal(node.right)

    # Add this method to the RestaurantAVL class in restaurant.py
    def get_all_restaurants(self):
        return self._inorder_traversal(self.root)

    def search_by_rating(self, rating):
        return self._search_by_rating(self.root, rating)

    def _search_by_rating(self, current, rating):
        if not current:
            return None
        if current.rating == rating:
            return current
        elif rating < current.rating:
            return self._search_by_rating(current.left, rating)
        else:
            return self._search_by_rating(current.right, rating)

    def print_tree(self):
        def _print_tree(node, level=0):
            if node:
                _print_tree(node.right, level + 1)
                print(' ' * 4 * level + '->', node.name, f"Rating: {node.rating}")
                _print_tree(node.left, level + 1)

        _print_tree(self.root)


def test():
    restaurant_tree = RestaurantAVL()

    print()
    restaurant_tree.add_restaurant("鄰家早午餐", 4.5, 230)
    restaurant_tree.print_tree()
    print()
    restaurant_tree.add_restaurant("gogobus", 4.8, 447)
    restaurant_tree.print_tree()
    print()
    restaurant_tree.add_restaurant("明哥滷味(忠孝)", 4.6, 520)
    restaurant_tree.print_tree()
    print()
    restaurant_tree.add_restaurant("品味", 3.9, 26)
    restaurant_tree.print_tree()
    print()
    restaurant_tree.add_restaurant("龍哥", 3.6, 120)
    restaurant_tree.print_tree()
    print()
    restaurant_tree.add_restaurant("沒料鐵哥", 2.9, 364)
    restaurant_tree.print_tree()

    result = restaurant_tree.search_by_rating(4.66)
    if result:
        print(f"找到餐廳: {result.name}, 評分: {result.rating}")
    else:
        print("找不到該評分的餐廳")
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from users.serializers import UserSerializer

User = get_user_model()

class FriendRequestView(APIView):
	permission_classes = (IsAuthenticated,)

	def post(self, request, username):
		try:
			to_user = User.objects.get(username=username)
			from_user = request.user
			if to_user in from_user.blocked_users.all() or from_user in to_user.blocked_users.all():
				return Response({"error": "You can't send a friend request, BLOCKING ISSUES."}, status=status.HTTP_400_BAD_REQUEST)
			if to_user in from_user.friends.all():
				return Response({"error": "You are already friends with this user."}, status=status.HTTP_400_BAD_REQUEST)
			if to_user in from_user.outgoing_requests.all():
				return Response({"error": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)
			if from_user in to_user.outgoing_requests.all():
				return Response({"error": "This user has already sent you a friend request."}, status=status.HTTP_400_BAD_REQUEST)

			from_user.outgoing_requests.add(to_user)
			return Response({"message": "Friend request sent."}, status=status.HTTP_201_CREATED)

		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class FriendRequestResponseView(APIView):
	permission_classes = (IsAuthenticated,)

	def post(self, request, username):
		action = request.data.get('action')
		try:
			from_user = User.objects.get(username=username)
			to_user = request.user

			if action == 'accept':
				# Add each other to friends list
				to_user.friends.add(from_user)
				from_user.friends.add(to_user)
				# Remove from incoming and outgoing requests
				to_user.incoming_requests.remove(from_user)
				from_user.outgoing_requests.remove(to_user)
				return Response({"message": "Friend request accepted."}, status=status.HTTP_200_OK)
			
			# Remove from incoming and outgoing requests
			elif action == 'reject':
				to_user.incoming_requests.remove(from_user)
				from_user.outgoing_requests.remove(to_user)
				return Response({"message": "Friend request rejected."}, status=status.HTTP_200_OK)
			else:
				return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class CancelFriendRequestView(APIView):
	permission_classes = (IsAuthenticated,)

	def post(self, request, username):
		try:
			to_user = User.objects.get(username=username)
			from_user = request.user

			# Check if there's an outgoing request to cancel
			if to_user in from_user.outgoing_requests.all():
				from_user.outgoing_requests.remove(to_user)
				to_user.incoming_requests.remove(from_user)
				return Response({"message": "Friend request cancelled."}, status=status.HTTP_200_OK)
			else:
				return Response({"error": "No outgoing friend request found."}, status=status.HTTP_400_BAD_REQUEST)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class FriendListView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		friends = request.user.friends.all()
		serializer = UserSerializer(friends, many=True)
		return Response(serializer.data)

class FriendRequestListView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		incoming = request.user.incoming_requests.all()
		outgoing = request.user.outgoing_requests.all()
		incoming_serializer = UserSerializer(incoming, many=True)
		outgoing_serializer = UserSerializer(outgoing, many=True)
		return Response({
			"incoming": incoming_serializer.data,
			"outgoing": outgoing_serializer.data
		})


class BlockUserView(APIView):
	permission_classes = (IsAuthenticated,)

	def post(self, request, username):
		try:
			user_to_block = User.objects.get(username=username)
			if user_to_block == request.user:
				return Response({"error": "You cannot block yourself."}, status=status.HTTP_400_BAD_REQUEST)
			
			request.user.blocked_users.add(user_to_block)
			
			# Remove from friends if they were friends
			request.user.friends.remove(user_to_block)
			user_to_block.friends.remove(request.user)
			
			# Remove any existing friend requests
			request.user.incoming_requests.remove(user_to_block)
			request.user.outgoing_requests.remove(user_to_block)
			user_to_block.incoming_requests.remove(request.user)
			user_to_block.outgoing_requests.remove(request.user)
			
			return Response({"message": f"User {username} has been blocked."}, status=status.HTTP_200_OK)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class UnblockUserView(APIView):
	permission_classes = (IsAuthenticated,)

	def post(self, request, username):
		try:
			user_to_unblock = User.objects.get(username=username)
			if user_to_unblock not in request.user.blocked_users.all():
				return Response({"error": "This user is not blocked."}, status=status.HTTP_400_BAD_REQUEST)
			
			request.user.blocked_users.remove(user_to_unblock)
			return Response({"message": f"User {username} has been unblocked."}, status=status.HTTP_200_OK)
		except User.DoesNotExist:
			return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class BlockedUsersListView(APIView):
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		blocked_users = request.user.blocked_users.all()
		serializer = UserSerializer(blocked_users, many=True)
		return Response(serializer.data)